from django.contrib import admin
from accounts.models import (
    TechnicianProfile,
    TechnicianVerification,
    TechnicianLicense,
    Organization,
    OrganizationTechnician,
)


class TechnicianLicenseInline(admin.TabularInline):
    model = TechnicianLicense
    extra = 0
    fields = ("license_file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


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
    readonly_fields = ("created_at", "updated_at")
    inlines = (TechnicianLicenseInline,)

    fieldsets = (
        (
            "基础信息",
            {
                "fields": ("user", "real_name", "phone", "id_card_no", "gender", "created_at", "updated_at"),
            },
        ),
        (
            "职业信息",
            {
                "fields": ("work_years", "service_types", "service_areas", "bio"),
            },
        ),
        (
            "状态控制",
            {
                "fields": ("verification_status", "is_disabled", "is_recommended", "recommended_at"),
            },
        ),
        (
            "证件与材料",
            {
                "description": "形象照、健康证等非高频字段，默认折叠；身份证正反面请在「技师认证记录」中查看。",
                "fields": ("avatar", "health_cert"),
                "classes": ("collapse",),
            },
        ),
    )


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
    readonly_fields = ("submitted_at", "reviewed_at")

    fieldsets = (
        (
            "基础信息",
            {
                "fields": ("technician", "verification_type", "status", "submitted_at", "reviewed_at", "reviewed_by", "admin_note"),
            },
        ),
        (
            "证件与材料",
            {
                "description": "身份证与健康证影像，默认折叠。",
                "fields": ("id_card_front", "id_card_back", "health_cert"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "company_name",
        "contact_person",
        "contact_phone",
        "verification_status",
        "is_disabled",
        "updated_at",
    ]
    list_filter = ["verification_status", "is_disabled", "updated_at"]
    search_fields = ["company_name", "contact_person", "contact_phone", "user__username"]


@admin.register(OrganizationTechnician)
class OrganizationTechnicianAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "organization",
        "technician",
        "status",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = [
        "organization__company_name",
        "technician__real_name",
        "technician__phone"
    ]
