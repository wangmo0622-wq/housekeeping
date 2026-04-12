from django.http import HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from admin_portal.captcha_utils import create_captcha
from admin_portal.views import (
    AdminAdminUserDetailView,
    AdminAdminUsersView,
    AdminBannerDetailView,
    AdminBannersView,
    AdminChangePasswordView,
    AdminCurrentUserView,
    AdminDashboardView,
    AdminHotServiceDetailView,
    AdminHotServicesView,
    AdminListingAuditActionView,
    AdminListingDetailView,
    AdminListingsView,
    AdminMenuDetailView,
    AdminMenusView,
    AdminOperatorCategoryCRUDView,
    AdminOperatorCategoryDetailView,
    AdminOperatorCategoryTreeView,
    AdminProfileView,
    AdminRegisteredUserDetailView,
    AdminRegisteredUserResetPasswordView,
    AdminRegisteredUsersView,
    AdminServiceTypeDetailView,
    AdminServiceTypesView,
    AdminTechnicianDetailView,
    AdminTechniciansView,
    AdminTechnicianVerificationActionView,
    CaptchaTokenObtainPairView,
    captcha_refresh_view,
)


@csrf_exempt
def captcha_image_view(request, captcha_id):
    captcha_id, image_buffer = create_captcha(captcha_id)
    response = HttpResponse(image_buffer.getvalue(), content_type="image/png")
    response["X-Captcha-Id"] = captcha_id
    return response


urlpatterns = [
    path("auth/captcha/<str:captcha_id>", captcha_image_view, name="admin_captcha_image"),
    path("auth/captcha", captcha_refresh_view, name="admin_captcha_refresh"),
    path("auth/token", CaptchaTokenObtainPairView.as_view(), name="admin_token_obtain_pair"),
    path("dashboard", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("menus", AdminMenusView.as_view(), name="admin_menus"),
    path("menus/<int:menu_id>", AdminMenuDetailView.as_view(), name="admin_menu_detail"),
    path("categories/tree", AdminOperatorCategoryTreeView.as_view(), name="admin_categories_tree"),
    path("categories", AdminOperatorCategoryCRUDView.as_view(), name="admin_categories_create"),
    path("categories/<int:category_id>", AdminOperatorCategoryDetailView.as_view(), name="admin_categories_detail"),
    path("technicians", AdminTechniciansView.as_view(), name="admin_technicians_list"),
    path("technicians/<int:technician_id>", AdminTechnicianDetailView.as_view(), name="admin_technician_detail"),
    path("technicians/<int:technician_id>/verification/<str:action>", AdminTechnicianVerificationActionView.as_view(), name="admin_technician_verification_action"),
    path("listings", AdminListingsView.as_view(), name="admin_listings_list"),
    path("listings/<int:listing_id>/audit/<str:action>", AdminListingAuditActionView.as_view(), name="admin_listing_audit_action"),
    path("listings/<int:listing_id>", AdminListingDetailView.as_view(), name="admin_listing_detail"),
    path("service-types", AdminServiceTypesView.as_view(), name="admin_service_types"),
    path("service-types/<int:service_type_id>", AdminServiceTypeDetailView.as_view(), name="admin_service_type_detail"),
    path("banners", AdminBannersView.as_view(), name="admin_banners"),
    path("banners/<int:banner_id>", AdminBannerDetailView.as_view(), name="admin_banner_detail"),
    path("hot-services", AdminHotServicesView.as_view(), name="admin_hot_services"),
    path("hot-services/<int:hot_service_id>", AdminHotServiceDetailView.as_view(), name="admin_hot_service_detail"),
    path("registered-users", AdminRegisteredUsersView.as_view(), name="admin_registered_users"),
    path("registered-users/<int:user_id>", AdminRegisteredUserDetailView.as_view(), name="admin_registered_user_detail"),
    path("registered-users/<int:user_id>/reset-password", AdminRegisteredUserResetPasswordView.as_view(), name="admin_registered_user_reset_password"),
    path("admin-users", AdminAdminUsersView.as_view(), name="admin_admin_users"),
    path("admin-users/<int:user_id>", AdminAdminUserDetailView.as_view(), name="admin_admin_user_detail"),
    path("me", AdminCurrentUserView.as_view(), name="admin_current_user"),
    path("change-password", AdminChangePasswordView.as_view(), name="admin_change_password"),
    path("profile", AdminProfileView.as_view(), name="admin_profile"),
]
