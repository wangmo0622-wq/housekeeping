# Category: FK `parent` -> 整型 `parent_id`（0=一级，否则为父主键）

from django.db import migrations, models


def copy_parent_fk_to_tree_parent_id(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    for row in Category.objects.iterator():
        fk = row.parent_id
        new_pid = fk if fk is not None else 0
        Category.objects.filter(pk=row.pk).update(tree_parent_id=new_pid)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_alter_hotservice_icon"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="tree_parent_id",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(copy_parent_fk_to_tree_parent_id, noop),
        migrations.RemoveField(
            model_name="category",
            name="parent",
        ),
        migrations.RenameField(
            model_name="category",
            old_name="tree_parent_id",
            new_name="parent_id",
        ),
        migrations.AlterField(
            model_name="category",
            name="parent_id",
            field=models.PositiveIntegerField(
                db_index=True,
                default=0,
                help_text="0 表示一级分类；否则为父分类主键（须为一级）",
                verbose_name="父级ID",
            ),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["status", "parent_id"], name="catalog_cat_stat_parent_idx"),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["parent_id"], name="catalog_cat_parent_id_idx"),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(fields=("parent_id", "name"), name="catalog_category_parent_id_name_uniq"),
        ),
    ]
