from django.urls import path

from listings.views_tech import (
    TechnicianDeleteListingView,
    TechnicianMyListingsView,
    TechnicianProfileView,
    TechnicianSubmitVerificationView,
    TechnicianToggleListingStatusView,
    TechnicianUpdateListingView,
    TechnicianUploadImageView,
    TechnicianVerificationStatusView,
)

urlpatterns = [
    path("me/profile", TechnicianProfileView.as_view(), name="tech_profile"),
    path("me/verification", TechnicianSubmitVerificationView.as_view(), name="tech_submit_verification"),
    path("me/verification/status", TechnicianVerificationStatusView.as_view(), name="tech_verification_status"),
    path("me/listings", TechnicianMyListingsView.as_view(), name="tech_my_listings"),
    path("me/listings/<int:listing_id>", TechnicianUpdateListingView.as_view(), name="tech_update_listing"),
    path("me/listings/<int:listing_id>/delete", TechnicianDeleteListingView.as_view(), name="tech_delete_listing"),
    path("me/listings/<int:listing_id>/toggle", TechnicianToggleListingStatusView.as_view(), name="tech_toggle_listing"),
    path("upload/image", TechnicianUploadImageView.as_view(), name="tech_upload_image"),
]
