from datetime import datetime
from alipay import AliPay
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.generic import View
from django_redis import get_redis_connection
from django.conf import settings

from goods.models import GoodsSKU
from order.models import OrderGoods, OrderInfo
from user.models import Address
from utils.mixin import LoginRequiredMixin


class OrderPlaceView(LoginRequiredMixin, View):
    ''' 订单提交视图'''
    def post(self, request):
        ''' 提交订单页面显示'''
        # 获取登录的用户
        user = request.user

        # 获取参数
        sku_ids = request.POST.getlist("sku_ids")

        # 校验参数
        if not sku_ids:
            # 跳转到购物车页面
            return redirect(reverse("cart:show"))
        
        conn = get_redis_connection("default")
        cart_key = 'cart_%d' % user.id

        skus = list()
        total_count = 0
        total_price = 0
        # 便利sku_ids获取商品信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户所要购买的商品的数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price*int(count)
            # 动态给sku增加属性amount，保存购买商品的小计
            sku.count = int(count)
            sku.amount = amount

            skus.append(sku)
            # 累加计算商品总价格和总件数
            total_count += int(count)
            total_price += amount

        # 运费
        transit_price = 10
        # 实付款
        total_pay = transit_price + total_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)
        context = {
            'skus':skus,
            'total_count':total_count,
            'total_price':total_price,
            'transit_price':transit_price,
            'total_pay':total_pay,
            'addrs':addrs,
            'sku_ids':sku_ids,
        }

        # 使用模板
        return render(request, "place_order.html", context)


# 悲观锁
class OrderCommitView(View):
    ''' 订单提交视图类'''
    @transaction.atomic
    def post(self, request):
        ''' 提交订单'''
        # 获取登录用户
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0, 'errmsg':'用户未登录'})

        # 接受参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res':1, 'errmsg':'参数不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res':2, 'errmsg':'非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res':3, 'errmsg':'地址非法'})

        # 创建订单

        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        save_id = transaction.savepoint()    # 事务保存点

        try:
            # 向df_order_info表中添加一条数据
            order = OrderInfo.objects.create(order_id=order_id, user=user, addr=addr, pay_method=pay_method, total_count=total_count, total_price=total_price, transit_price=transit_price)

            # 连接redis数据库
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品信息
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)   # 设置锁
                except GoodsSKU.DoesNotExist:
                    transaction.rollback(save_id)   # 回滚到保存点
                    return JsonResponse({'res':4, 'errmsg':'商品不存在'})

                # 从redis中获取用户所要购买的商品的数量
                count = conn.hget(cart_key, sku_id)

                # 判断商品库存
                if int(count) > sku.stock:
                    transaction.rollback(save_id)   # 回滚到保存点
                    return JsonResponse({'res':6, 'errmsg':'商品库存不足'})

                # 向df_order_goods表中添加数据
                OrderGoods.objects.create(order=order, sku=sku, count=count, price=sku.price)

                # 更新商品库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # 累加计算订单商品的总数目和总价格
                amount = sku.price*int(count)
                total_count += int(count)
                total_price += amount

            # 更新订单信息表中的商品总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception:
            transaction.rollback(save_id)   # 回滚到保存点
            return JsonResponse({'res':7, 'errmsg':'下单失败'})

        transaction.savepoint_commit(save_id)
        # 清楚购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)        

        # 返回应答
        return JsonResponse({'res':5, 'errmsg':'创建成功'})

# 乐观锁(没写，下来研究)
class OrderCommitView1(View):
    ''' 订单提交视图类'''
    @transaction.atomic
    def post(self, request):
        ''' 提交订单'''
        # 获取登录用户
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0, 'errmsg':'用户未登录'})

        # 接受参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res':1, 'errmsg':'参数不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res':2, 'errmsg':'非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res':3, 'errmsg':'地址非法'})

        # 创建订单
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        save_id = transaction.savepoint()    # 事务保存点

        try:
            # 向df_order_info表中添加一条数据
            order = OrderInfo.objects.create(order_id=order_id, user=user, addr=addr, pay_method=pay_method, total_count=total_count, total_price=total_price, transit_price=transit_price)

            # 连接redis数据库
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.splite(',')
            for sku_id in sku_ids:
                # 获取商品信息
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)   # 设置锁
                except GoodsSKU.DoesNotExist:
                    transaction.rollback(save_id)   # 回滚到保存点
                    return JsonResponse({'res':4, 'errmsg':'商品不存在'})

                # 从redis中获取用户所要购买的商品的数量
                count = conn.hget(cart_key, sku_id)

                # 判断商品库存
                if int(count) > sku.stock:
                    transaction.rollback(save_id)   # 回滚到保存点
                    return JsonResponse({'res':6, 'errmsg':'商品库存不足'})

                # 向df_order_goods表中添加数据
                OrderGoods.objects.create(order=order, sku=sku, count=count, price=sku.price)

                # 更新商品库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # 累加计算订单商品的总数目和总价格
                amount = sku.price-int(count)
                total_count += int(count)
                total_price += amount

            # 更新订单信息表中的商品总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception:
            transaction.rollback(save_id)   # 回滚到保存点
            return JsonResponse({'res':7, 'errmsg':'下单失败'})

        transaction.savepoint_commit(save_id)
        # 清楚购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)        

        # 返回应答
        return JsonResponse({'res':5, 'errmsg':'创建成功'})

class OrderPayView(View):
    '''订单支付'''
    def post(self, request):
        '''订单支付'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0, 'errmsg':'用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res':1, 'errmsg':'无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res':2, 'errmsg':'订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        alipayconf = settings.ALIPAY
        alipay = AliPay(
            appid=alipayconf['appid'], # 应用id
            app_notify_url=alipayconf['app_notify_url'],  # 默认回调url
            app_private_key_string=open(alipayconf['app_private_key_string']).read(),
            alipay_public_key_string=open(alipayconf['alipay_public_key_string']).read(),
            sign_type=alipayconf['sign_type'],  # RSA 或者 RSA2
            debug=alipayconf['debug']  # 默认False
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price+order.transit_price # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 订单id
            total_amount=str(total_pay), # 支付总金额
            subject='天天生鲜%s'%order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':3, 'pay_url':pay_url})


class CheckPayView(View):
    '''查看订单支付的结果'''
    def post(self, request):
        '''查询支付结果'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        alipayconf = settings.ALIPAY
        alipay = AliPay(
            appid=alipayconf['appid'], # 应用id
            app_notify_url=alipayconf['app_notify_url'],  # 默认回调url
            app_private_key_string=open(alipayconf['app_private_key_string']).read(),
            alipay_public_key_string=open(alipayconf['alipay_public_key_string']).read(),
            sign_type=alipayconf['sign_type'],  # RSA 或者 RSA2
            debug=alipayconf['debug']  # 默认False
        )

        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)

            # response = {
            #         "trade_no": "2017032121001004070200176844", # 支付宝交易号
            #         "code": "10000", # 接口调用是否成功
            #         "invoice_amount": "20.00",
            #         "open_id": "20880072506750308812798160715407",
            #         "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #         ],
            #         "buyer_logon_id": "csq***@sandbox.com",
            #         "send_pay_date": "2017-03-21 13:29:17",
            #         "receipt_amount": "20.00",
            #         "out_trade_no": "out_trade_no15",
            #         "buyer_pay_amount": "20.00",
            #         "buyer_user_id": "2088102169481075",
            #         "msg": "Success",
            #         "point_amount": "0.00",
            #         "trade_status": "TRADE_SUCCESS", # 支付结果
            #         "total_amount": "20.00"
            # }

            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4 # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res':3, 'message':'支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                print(code)
                return JsonResponse({'res':4, 'errmsg':'支付失败'})


class CommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count*order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i) # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '') # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5 # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))
