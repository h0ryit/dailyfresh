from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
from goods.models import GoodsSKU

# ajax发起的请求都在后台
class CartAddView(View):
    ''' 购物车记录添加'''
    def post(self, request):
        ''' 购物车记录添加'''
        # 接受数据
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"res":0, "errmsg":"请先登录"})

        # 接受数据
        sku_id = request.POST.get("sku_id")
        count = request.POST.get("count")

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({"res":1, "errmsg":"数据不完整"})

        try:
            count = int(count)
        except ValueError:
            return JsonResponse({"res":2, "errmsg":"商品数目出错"})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"res":3, "errmsg":"商品不存在"})

        # 添加记录
        conn = get_redis_connection('default')
        cart_key = "cart_%d" % user.id
        

        cart_count = conn.hget(cart_key, sku_id)
        # cart_count = int(cart_count)
        # print(cart_count)
        if cart_count:
            count += int(cart_count)

        if count > sku.stock:
            return JsonResponse({"res":4, "errmsg":"商品库存不足"})


        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中用户的条目数
        total_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({"res":5, "errmsg":"添加成功", "total_count": total_count})


class CartInfoView(LoginRequiredMixin, View):
    ''' 购物车详情页面'''
    def get(self, request):
        ''' 访问购物车'''
        # 获取登录的用户
        user = request.user

        # 获取用户购物车中存在的信息
        conn = get_redis_connection("default")
        cart_key = "cart_%d" % user.id

        cart_dict = conn.hgetall(cart_key)


        skus = list()
        total_count = 0
        total_price = 0
        # 遍历获取商品信息
        for sku_id, count in cart_dict.items():
            # 根据商品id获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品小计
            amount = sku.price*int(count)
            # print(amount)

            # 动态给sku对象增加属性，保存商品小计,数量
            sku.amount = amount
            sku.count = int(count)

            skus.append(sku)

            total_count += int(total_count)
            total_price += amount

        context = {
            'total_count':total_count,
            'total_price':total_price,
            'skus':skus,
        }

        return render(request, "cart.html", context)


class CartUpdateView(View):
    ''' 购物车更新'''
    def post(self, request):
        ''' 购物车记录更新'''

        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"res":0, "errmsg":"请先登录"})

        # 接受数据
        sku_id = request.POST.get("sku_id")
        count = request.POST.get("count")

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({"res":1, "errmsg":"数据不完整"})

        try:
            count = int(count)
        except ValueError:
            return JsonResponse({"res":2, "errmsg":"商品数目出错"})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"res":3, "errmsg":"商品不存在"})

        # 业务处理
        conn = get_redis_connection("default")
        cart_key = "cart_%d" % user.id

        # 校验商品库存
        if count > sku.stock:
            return JsonResponse({"res":4, "errmsg":"商品库存不足"})

        # 更新
        conn.hset(cart_key, sku_id, count)

        return JsonResponse({"res":5, "errmsg":"更新成功"})


class CartDeleteView(View):
    ''' 购物车记录删除'''
    def post(self, request):
        ''' 删除请求'''

        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"res":0, "errmsg":"请先登录"})

        # 接受数据
        sku_id = request.POST.get("sku_id")

        # 数据校验
        if not sku_id:
            return JsonResponse({"res":1, "errmsg":"无效的商品ID"})

        try:
            GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"res":2, "errmsg":"商品不存在"})

        # 业务处理
        conn = get_redis_connection("default")
        cart_key = "cart_%d" % user.id

        conn.hdel(cart_key, sku_id)

        return JsonResponse({'res':3, 'errmsg':"删除成功"})
