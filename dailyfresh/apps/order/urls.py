from django.urls import path
from .views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView, CommentView

app_name = "order"
urlpatterns = [
    path("palce/", OrderPlaceView.as_view(), name="place"),     # 订单页面
    path("commit/", OrderCommitView.as_view(), name="commit"),  # 订单创建
    path("pay/", OrderPayView.as_view(), name='pay'),    # 订单支付
    path('check/', CheckPayView.as_view(), name='check'),    # 查看支付结果
    path('comment/<order_id>/', CommentView.as_view(), name='comment'),    # 评论

]