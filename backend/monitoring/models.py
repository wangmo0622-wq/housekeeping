from django.db import models
from django.contrib.auth.models import User

from accounts.models import TechnicianProfile
from listings.models import Listing


class CallAttempt(models.Model):
    """
    用户点击“拨打电话”按钮（跳转即记录）。
    不记录是否接通（因为用户侧拿不到结果）。
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="call_attempts")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="call_attempts")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="call_attempts")

    called_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=64, blank=True, default="mini_program")

    # 简单去重：同一用户/同一 listing 在短时间内重复点击，可由幂等键控制
    idempotency_key = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["user", "called_at"]),
            models.Index(fields=["technician", "called_at"]),
        ]
        verbose_name = "拨打留痕"
        verbose_name_plural = "拨打留痕"

    def __str__(self) -> str:
        return f"CallAttempt<{self.user_id}:{self.listing_id}>"


class AdminMonitoringCall(models.Model):
    """
    管理员监控拨打（可记录接通/不接通结果）。
    """

    class Result(models.TextChoices):
        REACHED = "reached", "接通"
        NOT_REACHED = "not_reached", "未接通"
        INVALID = "invalid", "信息不符/无效"

    operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_monitoring_calls")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="admin_monitoring_calls")
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_monitoring_calls")

    called_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=16, choices=Result.choices, default=Result.NOT_REACHED)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "管理员监控拨打"
        verbose_name_plural = "管理员监控拨打"

