from django.shortcuts import render, redirect, reverse
from django.core.paginator import Paginator
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from .models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from order.models import OrderGoods

class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示首页'''
        # 尝试从缓存中获取数据
        context = cache.get("index_page_data")
        if context is None:
            # 获取商品的种类信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for thetype in types: # GoodsType
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=thetype, display_type=1).order_by('index')
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=thetype, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                thetype.image_banners = image_banners
                thetype.title_banners = title_banners
            
            # 组织模板上下文
            context = {
                'types':types,
                'goods_banners':goods_banners,
                'promotion_banners':promotion_banners,
                
            }
            
            # 设置缓存
            cache.set("index_page_data", context, 60*60)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)

        # 使用模板
        return render(request, 'index.html', context)

class DetailView(View):
    ''' 商品详情页面''' 
    def get(self, request, goods_id):
        ''' 访问商品详情'''
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse("goods:index"))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment="")

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by("-create_time")[:2]
        
        # 获取同一个spu的其他商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            history_key = "history_%d" % user.id
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)

        # 模板上下文
        context = {
            "sku":sku,
            "types":types,
            "sku_orders":sku_orders,
            "cart_count":cart_count,
            "same_spu_skus":same_spu_skus,
            "new_skus":new_skus,
        }
        
        return render(request, "detail.html", context)

class ListView(View):
    ''' 商品列表页'''
    def get(self, request, type_id, page):
        ''' 请求商品页面'''
        # 获取种类信息
        try:
            thetype = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse("goods:index"))
        
        # 获取商品分类信息
        types = GoodsType.objects.all()

        # 获取排序的方式
        sort = request.GET.get("sort")
        
        if sort == "price":
            skus = GoodsSKU.objects.filter(type=thetype).order_by("price")
        elif sort == "hot":
            skus = GoodsSKU.objects.filter(type=thetype).order_by("-sales")
        else:
            skus = GoodsSKU.objects.filter(type=thetype).order_by("-id")

        # 获取分类商品的信息
        # sku = GoodsSKU.objects.filter(type=thetype)

        # 分页
        paginator = Paginator(skus, 1)
        try:
            page = int(page)
        except ValueError:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取单页数据
        skus_page = paginator.page(page)

        # 页面控制，只显示5页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            range(page-2, page+3)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=thetype). order_by("-create_time")[:2]

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        context = {
            "type":thetype,
            "types":types,
            "skus_page":skus_page,
            "new_skus":new_skus,
            "pages":pages,
            "cart_count":cart_count,
        }

        return render(request, "list.html", context)
