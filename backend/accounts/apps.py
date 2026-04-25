from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self):
        # 注册一致性检查（postgresql_env_consistency 等）
        from . import checks  # noqa: F401
