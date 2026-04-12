from django.db import models
from django.contrib.auth.models import User


class AdminMenu(models.Model):
    name = models.CharField("菜单名称", max_length=64)
    key = models.CharField("页面键", max_length=64, blank=True, default="")
    path = models.CharField("路径", max_length=255, blank=True, default="")
    icon = models.TextField("图标", blank=True, default="")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="父菜单",
    )
    is_section = models.BooleanField("是否分组", default=False)
    sort_order = models.IntegerField("排序", default=0)
    is_visible = models.BooleanField("是否显示", default=True)
    is_enabled = models.BooleanField("是否启用", default=True)
    allow_all_staff = models.BooleanField("允许所有管理员", default=True)
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="admin_menus",
        verbose_name="指定可见用户",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_menu"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

