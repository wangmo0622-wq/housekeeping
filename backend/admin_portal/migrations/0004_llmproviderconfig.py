from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_portal", "0003_sitedocument"),
    ]

    operations = [
        migrations.CreateModel(
            name="LLMProviderConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("alibaba", "阿里"), ("siliconflow", "硅基流动"), ("deepseek", "DeepSeek")], max_length=24, unique=True, verbose_name="提供商")),
                ("display_name", models.CharField(default="", max_length=50, verbose_name="显示名称")),
                ("api_key", models.CharField(blank=True, default="", max_length=255, verbose_name="API Key")),
                ("base_url", models.CharField(blank=True, default="", max_length=255, verbose_name="接口地址")),
                ("model_name", models.CharField(blank=True, default="", max_length=120, verbose_name="模型名")),
                ("is_enabled", models.BooleanField(default=True, verbose_name="是否启用")),
                ("is_active", models.BooleanField(default=False, verbose_name="当前生效")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "大模型提供商配置",
                "verbose_name_plural": "大模型提供商配置",
                "db_table": "llm_provider_config",
            },
        ),
    ]
