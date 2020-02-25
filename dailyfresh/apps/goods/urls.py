from django.urls import path
from .views import IndexView, DetailView, ListView

app_name = 'goods'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path("goods/<goods_id>", DetailView.as_view(), name="detail"),
    path("list/<type_id>/<page>", ListView.as_view(), name="list"),
]