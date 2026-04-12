from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import LogoutView, WechatLoginView, PhoneRegisterView, PhoneLoginView, UserProfileView

urlpatterns = [
    path("wechat-login", WechatLoginView.as_view(), name="wechat_login"),
    path("phone-register", PhoneRegisterView.as_view(), name="phone_register"),
    path("phone-login", PhoneLoginView.as_view(), name="phone_login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile", UserProfileView.as_view(), name="user_profile"),
]