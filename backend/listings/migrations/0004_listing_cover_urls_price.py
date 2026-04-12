from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0003_alter_listing_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="cover_urls",
            field=models.JSONField(blank=True, default=list, verbose_name="封面图 URLs"),
        ),
        migrations.AddField(
            model_name="listing",
            name="listing_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="服务价格",
            ),
        ),
        migrations.AddField(
            model_name="listing",
            name="listing_price_unit",
            field=models.CharField(
                blank=True,
                default="次",
                max_length=16,
                verbose_name="服务计价单位",
            ),
        ),
    ]
