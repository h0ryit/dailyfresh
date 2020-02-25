from django.db import models


class BaseModel(models.Model):
    '''模型抽象基类'''

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')

    # class Meta做为嵌套类，主要目的是给上级类添加一些功能，或者指定一些标准。
    class Meta:
        # abstract将该基类定义为抽象类，即不必生成数据库表单，只作为一个可以继承的基类，把一些子类必须的代码放在基类，避免重复代码也避免重复录入数据库。
        abstract = True