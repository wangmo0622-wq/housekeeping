"""
开发期一致性检查：避免因未配置 .env 导致本机 manage.py 与 Docker 连的不是同一套库。
"""
from django.conf import settings
from django.core.checks import Warning, register


@register()
def postgresql_env_consistency(app_configs, **kwargs):
    """本机连 localhost 时若密码为空，极易与 Compose 内库不一致。"""
    hints = []
    db = settings.DATABASES.get("default") or {}
    engine = (db.get("ENGINE") or "").lower()
    if "postgresql" not in engine:
        return hints

    host = (db.get("HOST") or "").strip() or "localhost"
    password = db.get("PASSWORD")
    if host in ("localhost", "127.0.0.1") and not password:
        hints.append(
            Warning(
                "当前 PostgreSQL 密码为空且 HOST 为本机。若 Docker 里 db 使用非空密码，"
                "请复制项目根目录 .env.example 为 .env，并设置与 compose 一致的 POSTGRES_PASSWORD。",
                hint="运行 python manage.py show_database 查看当前解析到的连接信息。",
                id="accounts.W001",
            )
        )
    return hints
