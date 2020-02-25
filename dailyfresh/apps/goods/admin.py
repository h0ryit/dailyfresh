from django.contrib import admin

from goods.tasks import generate_static_index_html
from django.core.cache import cache
from .models import GoodsType, IndexPromotionBanner, IndexTypeGoodsBanner, IndexGoodsBanner, GoodsSKU, GoodsImage, Goods


class BaseModelAdmin(admin.ModelAdmin):
    """ 抽象父管理类"""
    def save_model(self, request, obj, form, change):
        ''' 新增或更新表中数据时调用，重写'''
        super().save_model(request, obj, form, change)

        # 重新生成静态文件
        generate_static_index_html.delay()

        # 清除首页的缓存数据
        cache.delete("index_page_data")

    def delete_model(self, request, obj):
        ''' 删除表中数据时调用'''
        super().delete_model(request, obj)
        generate_static_index_html.delay()

        cache.delete("index_page_data")



class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass

class GoodsTypeAdmin(BaseModelAdmin):
    pass

class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass

class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass

class GoodsSKUAdmin(BaseModelAdmin):
    pass

class GoodsImageAdmin(BaseModelAdmin):
    pass

class GoodsAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsImage, GoodsImageAdmin)
