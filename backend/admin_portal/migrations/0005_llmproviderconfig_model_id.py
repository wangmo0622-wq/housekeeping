from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_portal", "0004_llmproviderconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmproviderconfig",
            name="model_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="下拉选择预置模型ID，或手动输入自定义模型",
                max_length=64,
                verbose_name="模型ID",
            ),
        ),
    ]