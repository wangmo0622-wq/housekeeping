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


class SiteDocument(models.Model):
    class DocType(models.TextChoices):
        TERMS = "terms", "服务协议"
        PRIVACY = "privacy", "隐私政策"

    doc_type = models.CharField("文档类型", max_length=20, choices=DocType.choices, unique=True)
    title = models.CharField("标题", max_length=120, default="")
    content = models.TextField("内容", blank=True, default="")
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "site_document"
        verbose_name = "站点文档"
        verbose_name_plural = "站点文档"

    def __str__(self):
        return f"{self.get_doc_type_display()}({self.doc_type})"


class LLMProviderConfig(models.Model):
    class Provider(models.TextChoices):
        ALIBABA = "alibaba", "阿里"
        SILICONFLOW = "siliconflow", "硅基流动"
        DEEPSEEK = "deepseek", "DeepSeek"

    class ModelID(models.TextChoices):
        QWEN_PLUS = "qwen-plus", "通义千问-plus"
        QWEN_MAX = "qwen-max", "通义千问-max"
        QWEN_LONG = "qwen-long", "通义千问-long"
        DEEPSEEK_CHAT = "deepseek-chat", "DeepSeek-Chat"
        DEEPSEEK_V3 = "deepseek-v3", "DeepSeek-V3"
        DEEPSEEK_R1 = "deepseek-r1", "DeepSeek-R1"
        DEEPSEEK_R1_DISTILL_QWEN_7B = "deepseek-r1-distill-qwen-7b", "DeepSeek-R1-Distill-Qwen-7B"
        DEEPSEEK_R1_DISTILL_llAMA_8B = "deepseek-r1-distill-llama-8b", "DeepSeek-R1-Distill-Llama-8B"
        SILICON_DEEPSEEK_V3 = "deepseek-ai/DeepSeek-V3", "硅基流动-DeepSeek-V3"
        SILICON_DEEPSEEK_R1 = "deepseek-ai/DeepSeek-R1", "硅基流动-DeepSeek-R1"
        SILICON_QWEN_PLUS = "Qwen/Qwen-plus", "硅基流动-通义千问-plus"
        SILICON_QWEN_MAX = "Qwen/Qwen-max", "硅基流动-通义千问-max"

    provider = models.CharField("提供商", max_length=24, choices=Provider.choices, unique=True)
    display_name = models.CharField("显示名称", max_length=50, default="")
    api_key = models.CharField("API Key", max_length=255, blank=True, default="")
    base_url = models.CharField("接口地址", max_length=255, blank=True, default="")
    model_name = models.CharField("模型名", max_length=120, blank=True, default="")
    model_id = models.CharField("模型ID", max_length=64, blank=True, default="", help_text="下拉选择预置模型ID，或手动输入自定义模型")
    is_enabled = models.BooleanField("是否启用", default=True)
    is_active = models.BooleanField("当前生效", default=False)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "llm_provider_config"
        verbose_name = "大模型提供商配置"
        verbose_name_plural = "大模型提供商配置"

    def __str__(self):
        return f"{self.display_name or self.provider}({self.provider})"

