from django.urls import path

from accounts.views_web import (
    OrganizationPortalConsoleView,
    OrganizationPortalHomeView,
    OrganizationPortalLoginView,
    OrganizationPortalRegisterStep2View,
)


urlpatterns = [
    path("", OrganizationPortalHomeView.as_view(), name="organization_portal_home"),
    path("login/", OrganizationPortalLoginView.as_view(), name="organization_portal_login_alias"),
    path("register-step2/", OrganizationPortalRegisterStep2View.as_view(), name="organization_portal_register_step2"),
    path("console/", OrganizationPortalConsoleView.as_view(), name="organization_portal_console"),
]

