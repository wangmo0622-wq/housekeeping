from django.contrib import admin
from catalog.models import Category, ServiceType, Banner


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "parent_id", "sort_order", "status", "updated_at"]
    list_filter = ["status"]
    search_fields = ["name"]


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "category",
        "base_price",
        "currency",
        "price_unit",
        "status",
        "updated_at",
    ]
    list_filter = ["status", "category"]
    search_fields = ["name"]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "image_url", "link_type", "link_value", "sort_order", "status", "created_at"]
    list_filter = ["status", "link_type"]
    search_fields = ["title"]
    list_editable = ["sort_order", "status"]
