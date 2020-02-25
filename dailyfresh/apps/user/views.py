import re

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render, reverse
from django.views.generic import View
from django_redis import get_redis_connection
from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from goods.models import GoodsSKU
from order.models import OrderGoods, OrderInfo
from utils.mixin import LoginRequiredMixin

from .models import Address, User
from .tasks import send_register_active_email


class RegisterView(View):
    ''' 注册'''
    def get(self, request):
        ''' 访问注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        ''' 处理注册请求'''
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据是否合法
        ret = self.CheckRquest(user_name, pwd, cpwd, email, allow)
        if not ret[0]:
            return render(request, 'register.html', ret[1])

        # 进行注册
        user = User.objects.create_user(user_name, email, pwd)
        user.is_active = 0
        user.save()

        # 发送激活邮件
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info).decode('utf8')
        send_register_active_email.delay(email, user_name, token)

        return redirect(reverse('user:login'))

    def CheckRquest(self, username, pwd, cpwd, email, allow):
        ''' 检验数据合法性'''

        # 是否同意协议
        if allow != "on":
            return (False, {'errmsg': '请同意用户协议'})

        # 校验数据完整性
        if not all([username, pwd, email, cpwd]):
            return (False, {'errmsg': '数据不完整'})

        # 校验密码输入是否一致
        if pwd != cpwd:
            return (False, {'errmsg': '密码不一致'})

        # 校验邮箱
        # if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        #     return (False, {'errmsg': '邮箱不合法'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            # 用户名已存在
            return (False, {'errmsg': '用户名已存在'})


        return (True, {})

class LoginView(View):
    ''' 登录'''
    def get(self, request):
        ''' 访问登录页面'''

        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = "checked"
        else:
            username = ""
            checked = ""

        return render(request, 'login.html', {"username":username, "checked":checked})

    def post(self, request):
        ''' 处理登录请求'''
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 设置登录后要跳转的页面
        next_url = request.GET.get("next", reverse("goods:index"))
        response = redirect(next_url)

        # 校验数据
        ret = self.CheckDatas(username, pwd)
        if not ret[0]:
            return render(request, "login.html", ret[1])

        # 创建session
        login(request, ret[1])

        # 记住用户名
        if remember == "on":
            response.set_cookie('username', username, max_age=7*3600*24)
        else:
            response.delete_cookie('username')

        return response

    def CheckDatas(self, username, pwd):
        ''' 校验数据'''
        user = authenticate(username=username, password=pwd)
        # print(user.username, user.is_active)
        if user is None:
            return (False, {"errmsg":"登录失败"})

        if not user.is_active:
            return (False, {"errmsg":"用户未激活"})

        return (True, user)

class LogoutView(View):
    ''' 退出登录'''
    def get(self, request):
        ''' 退出登录'''
        logout(request)
        return redirect(reverse("goods:index"))

class ActiveView(View):
    ''' 用户激活'''
    def get(self, request, token):
        ''' 用户激活'''
        # 进行解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)

            user_id = info['confirm']

            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')

class UserInfoView(LoginRequiredMixin, View):
    ''' 用户中心-信息页'''
    def get(self, request):
        ''' 访问页面'''
        # 获取用户个人信息
        user = request.user
        address = Address.objects.get_default_address(user)


        # 获取用户历史浏览记录
        conn = get_redis_connection('default')
        history_key = "history_%d" % user.id
        sku_ids = conn.lrange(history_key, 0, 4)

        goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        context = {"page":"user", "address":address, "goods_li":goods_li}
        
        return render(request, "user_center_info.html", context)

class UserOrderView(LoginRequiredMixin, View):
    ''' 用户中心-订单页'''
    def get(self, request, page):
        ''' 访问页面'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by("-create_time")

        # 遍历获取订单商品信息
        for order in orders:
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 便利order_skus计算商品小计
            for order_sku in order_skus:
                amount = order_sku.count*order_sku.price
                order_sku.amount = amount
            
            # 保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

            order.order_skus = order_skus

            order.total_price_2 = order.total_price+order.transit_price

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except ValueError:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order_page':order_page,
            'pages':pages,
            'page': 'order',
        }

        return render(request, "user_center_order.html", context)

class UserAddressView(LoginRequiredMixin, View):
    ''' 用户中心-地址页'''
    def get(self, request):
        ''' 访问页面'''
        # 获取用户默认收获地址
        user = request.user
        address = Address.objects.get_default_address(user)

        return render(request, "user_center_site.html", {"page":"address", "address":address})

    def post(self, request):
        """ 添加地址"""
        # 接受数据
        receive = request.POST.get("receive")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")

        # 校验数据
        ret = self.CheckAddress(receive, addr, phone)
        if not ret[0]:
            return render(request, "user_center_site.html", ret[1])

        # 获取当前用户
        user = request.user
        # 判断是否已存在默认地址
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 创建地址信息
        Address.objects.create(user=user, receive=receive, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)

        return redirect(reverse("user:address"))

    def CheckAddress(self, receive, addr, phone):
        if not all([receive, addr, phone]):
            return (False, {"errmsg":"收件人，地址，电话不可为空"})

        if not re.match(r"^1[3|4|5|7|8][0-9]{9}$", phone):
            return (False, {"errmsg":"手机号不规范"})



        return (True, {})
