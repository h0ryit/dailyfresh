'''使用celery'''

from __future__ import absolute_import, unicode_literals

import os

from celery import shared_task
from django.conf import settings
from django.template import loader
from .models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


@shared_task
def generate_static_index_html():
    ''' 产生首页静态页面'''
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

    # 使用模板
    temp = loader.get_template('static_index.html')
    # htmlcontext = RequestContext(request, context)
    html = temp.render(context)

    # 生成对应的静态页面
    save_path = settings.STATIC_ROOT + "/index.html"
    save_path = os.path.join(settings.BASE_DIR, save_path)
    with open(save_path, "w") as f:
        f.write(html)
