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
