from django.urls import path
from admin_portal.views_web import (
    AdminPortalIndexView,
    AdminPortalLoginView,
    AdminPortalPageView,
)


urlpatterns = [
    path("", AdminPortalIndexView.as_view(), name="admin_portal_index"),
    path("login/", AdminPortalLoginView.as_view(), name="admin_portal_login"),
    path("dashboard/", AdminPortalPageView.as_view(), {"page_key": "dashboard"}, name="admin_portal_dashboard"),
    path("categories/", AdminPortalPageView.as_view(), {"page_key": "categories"}, name="admin_portal_categories"),
    path("technicians/", AdminPortalPageView.as_view(), {"page_key": "technicians"}, name="admin_portal_technicians"),
    path("organizations/", AdminPortalPageView.as_view(), {"page_key": "organizations"}, name="admin_portal_organizations"),
    path("listings/", AdminPortalPageView.as_view(), {"page_key": "listings"}, name="admin_portal_listings"),
    path("banners/", AdminPortalPageView.as_view(), {"page_key": "banners"}, name="admin_portal_banners"),
    path("hot-services/", AdminPortalPageView.as_view(), {"page_key": "hot_services"}, name="admin_portal_hot_services"),
    path("registered-users/", AdminPortalPageView.as_view(), {"page_key": "registered_users"}, name="admin_portal_registered_users"),
    path("admin-users/", AdminPortalPageView.as_view(), {"page_key": "admin_users"}, name="admin_portal_admin_users"),
    path("menus/", AdminPortalPageView.as_view(), {"page_key": "menus"}, name="admin_portal_menus"),
    path("legal-docs/", AdminPortalPageView.as_view(), {"page_key": "legal_docs"}, name="admin_portal_legal_docs"),
    path("legal-terms/", AdminPortalPageView.as_view(), {"page_key": "legal_terms"}, name="admin_portal_legal_terms"),
    path("legal-privacy/", AdminPortalPageView.as_view(), {"page_key": "legal_privacy"}, name="admin_portal_legal_privacy"),
    path("llm-providers/", AdminPortalPageView.as_view(), {"page_key": "llm_providers"}, name="admin_portal_llm_providers"),
    path("change-password/", AdminPortalPageView.as_view(), {"page_key": "change_password"}, name="admin_portal_change_password"),
    path("profile/", AdminPortalPageView.as_view(), {"page_key": "profile"}, name="admin_portal_profile"),
]
