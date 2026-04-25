# 下线「菜单管理」侧栏项：删除 key=menus 的 AdminMenu 记录

from django.db import migrations


def remove_menus_nav_item(apps, schema_editor):
    AdminMenu = apps.get_model("admin_portal", "AdminMenu")
    AdminMenu.objects.filter(key="menus").delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("admin_portal", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(remove_menus_nav_item, noop_reverse),
    ]
