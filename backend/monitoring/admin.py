from django.contrib import admin
from monitoring.models import AdminMonitoringCall, CallAttempt


@admin.register(CallAttempt)
class CallAttemptAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "technician", "listing", "called_at", "source"]
    list_filter = ["source", "called_at"]
    search_fields = ["user__username", "technician__real_name"]


@admin.register(AdminMonitoringCall)
class AdminMonitoringCallAdmin(admin.ModelAdmin):
    list_display = ["id", "operator", "technician", "result", "called_at"]
    list_filter = ["result", "called_at"]
    search_fields = ["technician__real_name"]
