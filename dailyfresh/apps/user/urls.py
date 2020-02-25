from django.urls import path
from .views import RegisterView, ActiveView, LoginView, UserOrderView, UserInfoView, UserAddressView,LogoutView

app_name = 'user'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('active/<token>/', ActiveView.as_view(), name='active'),
    path('login/', LoginView.as_view(), name='login'),
    path("order/<page>/", UserOrderView.as_view(), name="order"),
    path("address/", UserAddressView.as_view(), name="address"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", UserInfoView.as_view(), name="user"),
]