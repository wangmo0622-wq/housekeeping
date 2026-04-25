import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "创建或更新可登录「自定义管理后台」(/admin/) 的账号：is_staff=True。"
        "（与 Django 自带 /django-admin/ 无关；本项目未挂载 django.contrib.admin 的默认后台 URL。）"
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin", help="用户名，默认 admin")
        parser.add_argument(
            "--password",
            default=None,
            help="密码；也可通过环境变量 ADMIN_BOOTSTRAP_PASSWORD 传入（二者选一）",
        )

    def handle(self, *args, **options):
        username = (options["username"] or "").strip()
        password = options["password"] or os.environ.get("ADMIN_BOOTSTRAP_PASSWORD")
        if not username:
            self.stderr.write(self.style.ERROR("username 不能为空"))
            return
        if not password:
            self.stderr.write(
                self.style.ERROR(
                    "请指定密码：\n"
                    "  python manage.py bootstrap_admin --password '你的密码'\n"
                    "或设置环境变量 ADMIN_BOOTSTRAP_PASSWORD 后不带 --password 再执行。"
                )
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        action = "已创建" if created else "已更新"
        self.stdout.write(self.style.SUCCESS(f"{action} 管理员：{username}（可登录 /admin/login/）"))
