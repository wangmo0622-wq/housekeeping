from django.db import models
from django.contrib.auth.models import User

from accounts.models import TechnicianProfile
from catalog.models import Category, ServiceType


class Listing(models.Model):
    """
    技师发布信息（以内容为中心）。

    公共端门禁：
    - listing.status == published
    - technician_profile.verification_status == approved
    - technician_profile.is_disabled == False

    详情页（含拨号）只对满足门禁的 Listing 返回。
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PENDING = "pending", "待审核"
        PUBLISHED = "published", "已发布"
        REJECTED = "rejected", "驳回"
        DISABLED = "disabled", "下架"

    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="listings", verbose_name="技师")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="listings", verbose_name="分类")
    services = models.ManyToManyField(ServiceType, blank=True, related_name="listings", verbose_name="服务类型")

    title = models.CharField(max_length=128, verbose_name="标题")
    description = models.TextField(blank=True, verbose_name="描述")

    # 首张封面与兼容旧接口；多图见 cover_urls（最多 MAX_COVER_URLS 张，与小程序一致）
    cover_url = models.URLField(blank=True, default="", verbose_name="封面图 URL")
    cover_urls = models.JSONField(default=list, blank=True, verbose_name="封面图 URLs")

    # 技师填写的标价（可选）；未填时小程序可展示关联服务类型的价格
    listing_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="服务价格"
    )
    listing_price_unit = models.CharField(
        max_length=16, default="次", blank=True, verbose_name="服务计价单位"
    )
    service_areas = models.TextField(
        blank=True,
        verbose_name="服务区域",
        help_text="可服务区域，多选，以逗号分隔",
    )

    contact_info = models.CharField(max_length=128, blank=True, verbose_name="联系方式", help_text="服务的联系方式，不一定是注册手机号")

    is_deleted = models.BooleanField(default=False, verbose_name="已删除")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, verbose_name="审核状态")

    audit_note = models.TextField(blank=True, verbose_name="审核意见")
    audited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="审核人")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    MAX_COVER_URLS = 6

    def save(self, *args, **kwargs):
        if not isinstance(self.cover_urls, list):
            self.cover_urls = []
        if not self.cover_urls and self.cover_url:
            self.cover_urls = [self.cover_url]
        self.cover_urls = [
            str(u).strip() for u in self.cover_urls if u and str(u).strip()
        ][: self.MAX_COVER_URLS]
        if self.cover_urls:
            self.cover_url = self.cover_urls[0]
        else:
            self.cover_url = ""
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["status", "category"]),
            models.Index(fields=["technician", "status"]),
        ]

    def __str__(self) -> str:
        return f"Listing<{self.id}><{self.title}>"

    class Meta:
        verbose_name = "发布信息"
        verbose_name_plural = "发布信息"


class ListingAudit(models.Model):
    """
    服务审核记录（保留历史）。
    """

    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        PUBLISHED = "published", "已发布"
        REJECTED = "rejected", "驳回"
        DISABLED = "disabled", "下架"

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="audits"
    )
    status = models.CharField(max_length=16, choices=Status.choices, verbose_name="审核状态")
    audit_note = models.TextField(blank=True, verbose_name="审核意见")
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="审核时间")
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="审核人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self) -> str:
        return f"ListingAudit<{self.listing_id}:{self.status}>"

    class Meta:
        verbose_name = "服务审核记录"
        verbose_name_plural = "服务审核记录"
        ordering = ["-created_at"]
