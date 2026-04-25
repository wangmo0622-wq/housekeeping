from django.contrib import admin
from listings.models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "technician",
        "category",
        "listing_price",
        "status",
        "published_at",
        "reviewed_at",
        "updated_at",
    ]
    list_filter = ["status", "category", "technician"]
    search_fields = ["title", "description"]
    
    fieldsets = (
        (
            "基础信息",
            {
                "fields": ("technician", "category", "services", "title", "description"),
            },
        ),
        (
            "价格与区域",
            {
                "fields": ("listing_price", "listing_price_unit", "service_areas", "contact_info"),
            },
        ),
        (
            "多媒体与展示",
            {
                "description": "封面与非高频编辑字段，默认折叠。",
                "fields": ("cover_url", "cover_urls"),
                "classes": ("collapse",),
            },
        ),
        (
            "审核与状态控制",
            {
                "fields": ("status", "is_deleted", "audit_note", "audited_by", "reviewed_at", "published_at"),
            },
        ),
    )
    readonly_fields = ("reviewed_at", "published_at")
    filter_horizontal = ("services",)
