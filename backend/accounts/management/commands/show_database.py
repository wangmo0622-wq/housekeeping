"""打印当前 Django 解析到的 default 数据库连接（不含密码）。"""
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "显示 DATABASES['default'] 的 host/name/user/port（用于核对与 Docker 是否同一库）"

    def handle(self, *args, **options):
        db = settings.DATABASES.get("default") or {}
        self.stdout.write("default 数据库（来自环境变量 / .env）：")
        self.stdout.write(f"  ENGINE: {db.get('ENGINE')}")
        self.stdout.write(f"  NAME:   {db.get('NAME')}")
        self.stdout.write(f"  USER:   {db.get('USER')}")
        self.stdout.write(f"  HOST:   {db.get('HOST')}")
        self.stdout.write(f"  PORT:   {db.get('PORT')}")
        pwd = db.get("PASSWORD")
        self.stdout.write(f"  PASSWORD: {'(已设置)' if pwd else '(空)'}")
