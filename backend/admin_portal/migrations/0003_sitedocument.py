from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin_portal", "0002_remove_menus_from_sidebar"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("doc_type", models.CharField(choices=[("terms", "服务协议"), ("privacy", "隐私政策")], max_length=20, unique=True, verbose_name="文档类型")),
                ("title", models.CharField(default="", max_length=120, verbose_name="标题")),
                ("content", models.TextField(blank=True, default="", verbose_name="内容")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "站点文档",
                "verbose_name_plural": "站点文档",
                "db_table": "site_document",
            },
        ),
    ]
