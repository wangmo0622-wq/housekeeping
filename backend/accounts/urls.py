from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    LogoutView, WechatLoginView, PhoneRegisterView, PhoneLoginView, UserProfileView,
    OrganizationRegisterView, OrganizationLoginView, OrganizationProfileView,
    OrganizationTechnicianView, OrganizationTechnicianRegisterView,
    OrganizationVerificationSubmitView, TechnicianUnbindOrganizationRequestView,
    OrganizationTechnicianUnbindActionView, TechnicianOrganizationRelationListView,
    OrganizationDashboardView, OrganizationMessagesView, OrganizationServicesView,
    RegionDictView, OrganizationChangePasswordView,
)

urlpatterns = [
    # 普通用户/技师相关
    path("wechat-login", WechatLoginView.as_view(), name="wechat_login"),
    path("phone-register", PhoneRegisterView.as_view(), name="phone_register"),
    path("phone-login", PhoneLoginView.as_view(), name="phone_login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile", UserProfileView.as_view(), name="user_profile"),
    path("regions", RegionDictView.as_view(), name="region_dict"),
    
    # 机构相关
    path("organization/register", OrganizationRegisterView.as_view(), name="organization_register"),
    path("organization/login", OrganizationLoginView.as_view(), name="organization_login"),
    path("organization/profile", OrganizationProfileView.as_view(), name="organization_profile"),
    path("organization/change-password", OrganizationChangePasswordView.as_view(), name="organization_change_password"),
    path("organization/verification/submit", OrganizationVerificationSubmitView.as_view(), name="organization_verification_submit"),
    path("organization/dashboard", OrganizationDashboardView.as_view(), name="organization_dashboard"),
    path("organization/messages", OrganizationMessagesView.as_view(), name="organization_messages"),
    path("organization/technicians/register", OrganizationTechnicianRegisterView.as_view(), name="organization_technician_register"),
    path("organization/technicians", OrganizationTechnicianView.as_view(), name="organization_technicians"),
    path("organization/technicians/<int:relation_id>/unbind-request", TechnicianUnbindOrganizationRequestView.as_view(), name="technician_unbind_organization_request"),
    path("organization/technicians/<int:relation_id>/unbind/<str:action>", OrganizationTechnicianUnbindActionView.as_view(), name="organization_technician_unbind_action"),
    path("organization/services", OrganizationServicesView.as_view(), name="organization_services"),
    path("technician/organizations", TechnicianOrganizationRelationListView.as_view(), name="technician_organization_relations"),
]