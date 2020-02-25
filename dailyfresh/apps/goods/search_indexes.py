from haystack import indexes
from .models import GoodsSKU

#指定对于某个类的某些数据建立索引
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    ''' 商品索引类'''

    text = indexes.CharField(document=True, use_template=True)  # 索引字段

    def get_model(self):
        return GoodsSKU

    # 建立索引的数据
    def index_queryset(self, using=None):
        return self.get_model().objects.all()
