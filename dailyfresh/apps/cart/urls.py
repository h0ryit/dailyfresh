from django.urls import path
from .views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = "cart"
urlpatterns = [
    path("add/", CartAddView.as_view(), name="add"),    # 添加购物车记录
    path("update/", CartUpdateView.as_view(), name="update"),    # 跟新购物车记录
    path("delete/", CartDeleteView.as_view(), name="delete"),       # 删除购物车
    path("", CartInfoView.as_view(), name="show"),      # 购物车页面显示
]
