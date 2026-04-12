from django.urls import path

from listings.views_public import (
    PublicCallAttemptCreateView,
    PublicCategoryTreeView,
    PublicListingDetailView,
    PublicListingsView,
    PublicTechniciansView,
    PublicTechnicianDetailView,
)
from listings.views_public_mini import (
    PublicBannerListView,
    PublicHotServiceListView,
    PublicServiceTypeListView,
    PublicCategoryServiceTypesView,
)

urlpatterns = [
    path("categories/tree", PublicCategoryTreeView.as_view(), name="public_category_tree"),
    path("listings", PublicListingsView.as_view(), name="public_listings"),
    path("listings/<int:listing_id>", PublicListingDetailView.as_view(), name="public_listing_detail"),
    path("call-attempts", PublicCallAttemptCreateView.as_view(), name="public_call_attempts_create"),
    path("banners", PublicBannerListView.as_view(), name="public_banners"),
    path("hot-services", PublicHotServiceListView.as_view(), name="public_hot_services"),
    path("service-types", PublicServiceTypeListView.as_view(), name="public_service_types"),
    path("categories/<int:category_id>/service-types", PublicCategoryServiceTypesView.as_view(), name="public_category_service_types"),
    path("technicians", PublicTechniciansView.as_view(), name="public_technicians"),
    path("technicians/<int:technician_id>", PublicTechnicianDetailView.as_view(), name="public_technician_detail"),
]