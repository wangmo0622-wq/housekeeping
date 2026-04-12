from django.contrib import admin
from accounts.models import TechnicianProfile, TechnicianVerification


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "real_name",
        "phone",
        "verification_status",
        "is_disabled",
        "updated_at",
    ]
    list_filter = ["verification_status", "is_disabled", "updated_at"]
    search_fields = ["real_name", "phone", "user__username"]


@admin.register(TechnicianVerification)
class TechnicianVerificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "technician",
        "verification_type",
        "status",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    ]
    list_filter = ["verification_type", "status", "submitted_at", "reviewed_at"]
    search_fields = ["technician__real_name", "technician__phone"]
