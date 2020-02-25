from django.db import models
from django.contrib.auth.models import AbstractUser     # 用户验证模块
from db.base_model import BaseModel


class User(AbstractUser):   # 继承默认用户模型，需在配置文件中设定AUTH_USER_MODEL
    ''' 用户模型类'''
    class Meta:
        db_table = 'df_user'    # 指定该类的数据库表单名字
        verbose_name = '用户'   # 指定对象显示的名字
        verbose_name_plural = verbose_name  # 对象名的复数形式


class AddressManager(models.Manager):
    ''' 地址模型管理器类'''
    def get_default_address(self, user):
        ''' 获取用户默认收货地址'''
        # self.model:获取self对象所在的模型类
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address = None
        return address

class Address(BaseModel):
    ''' 地址模型类'''
    user = models.ForeignKey('User', verbose_name='所属账户', on_delete=models.CASCADE)
    receive = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    # 自定义模型管理器
    objects = AddressManager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name