from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "catalog"

    def ready(self):
        from django.core.cache import cache
        from django.db.models.signals import post_delete, post_save

        from catalog.cache_keys import PUBLIC_CATEGORY_TREE_PAYLOAD_KEY
        from catalog.models import Category

        def bust_public_category_tree_cache(**kwargs):
            cache.delete(PUBLIC_CATEGORY_TREE_PAYLOAD_KEY)

        post_save.connect(bust_public_category_tree_cache, sender=Category)
        post_delete.connect(bust_public_category_tree_cache, sender=Category)
