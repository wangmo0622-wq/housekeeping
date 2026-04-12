from django.db import models


class Category(models.Model):
    """
    单表自关联：parent_id=0 为一级分类，非 0 为二级（值为父级主键）。
    业务层限制：二级下不得再挂子分类（最多两级）。
    """

    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    name = models.CharField(max_length=64, verbose_name="分类名称")
    parent_id = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="父级ID",
        help_text="0 表示一级分类；否则为父分类主键（须为一级）",
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ENABLED, verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        indexes = [
            models.Index(fields=["status", "parent_id"], name="catalog_cat_stat_parent_idx"),
            models.Index(fields=["parent_id"], name="catalog_cat_parent_id_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["parent_id", "name"], name="catalog_category_parent_id_name_uniq"),
        ]

    def __str__(self) -> str:
        return self.name

    def is_root(self) -> bool:
        return self.parent_id == 0


class Tag(models.Model):
    """
    服务标签（如：上门、深度清洁、带工具等）。
    """

    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    name = models.CharField(max_length=32, unique=True, verbose_name="标签名称")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ENABLED, verbose_name="状态"
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"

    def __str__(self) -> str:
        return self.name


class ServiceType(models.Model):
    """
    服务类型 / 价格 / 标签（后台"服务管理"对应这里）。
    """

    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    name = models.CharField(max_length=64, verbose_name="服务类型名称")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="service_types",
        help_text="用于和分类浏览关联（可选父/子类节点都可以）。",
    )

    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="基础价格")
    currency = models.CharField(max_length=8, default="CNY", verbose_name="币种")
    price_unit = models.CharField(
        max_length=16, default="per_service", help_text="计价单位（展示用）。", verbose_name="计价单位"
    )

    tags = models.ManyToManyField(Tag, blank=True, related_name="service_types", verbose_name="标签")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ENABLED, verbose_name="状态")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "服务类型"
        verbose_name_plural = "服务类型"

    def __str__(self) -> str:
        return self.name


class Banner(models.Model):
    """
    小程序首页轮播图
    """

    class LinkType(models.TextChoices):
        CATEGORY = "category", "分类"
        LISTING = "listing", "服务详情"
        URL = "url", "网页链接"
        NONE = "none", "无跳转"

    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    image = models.ImageField(
        upload_to="banners/",
        blank=True,
        null=True,
        verbose_name="图片",
        help_text="上传轮播图片",
    )
    image_url = models.URLField(max_length=500, blank=True, default="", verbose_name="图片URL")
    link_type = models.CharField(
        max_length=16,
        choices=LinkType.choices,
        default=LinkType.NONE,
        verbose_name="跳转类型",
    )
    link_value = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="跳转值",
        help_text="分类ID、服务ID或URL",
    )
    title = models.CharField(max_length=64, blank=True, default="", verbose_name="标题")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ENABLED, verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "sort_order"], name="catalog_ban_status_6816ce_idx"),
        ]
        ordering = ["sort_order", "-created_at"]
        verbose_name = "轮播图"
        verbose_name_plural = "轮播图"

    def __str__(self) -> str:
        return self.title or f"Banner-{self.id}"


class HotService(models.Model):
    """
    热门服务（小程序首页配置）
    """

    class Status(models.TextChoices):
        ENABLED = "enabled", "启用"
        DISABLED = "disabled", "停用"

    class LinkType(models.TextChoices):
        CATEGORY = "category", "分类"
        LISTING = "listing", "服务详情"
        URL = "url", "网页链接"
        NONE = "none", "无跳转"

    name = models.CharField(max_length=64, verbose_name="名称")
    icon = models.ImageField(upload_to="hot_services/icons/", blank=True, null=True, verbose_name="图标")
    link_type = models.CharField(
        max_length=16,
        choices=LinkType.choices,
        default=LinkType.NONE,
        verbose_name="跳转类型",
    )
    link_value = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="跳转值",
        help_text="分类ID、服务ID或URL",
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ENABLED, verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "sort_order"], name="catalog_hot_status_2e54ee_idx"),
        ]
        ordering = ["-sort_order", "-created_at"]
        verbose_name = "热门服务"
        verbose_name_plural = "热门服务"

    def __str__(self) -> str:
        return self.name
