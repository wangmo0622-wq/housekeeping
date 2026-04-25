"""
从仓库内 data/exported_data.json 恢复历史演示数据（dumpdata 导出格式）。
"""
import json
from pathlib import Path

from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "从 data/exported_data.json 导入演示数据；自动跳过 token_blacklist（当前未启用该应用）。"
        "建议在空库或备份后执行；若主键/唯一约束冲突会报错。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="JSON 路径，默认 BASE_DIR/data/exported_data.json",
        )

    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR)
        path = Path(options["path"]) if options["path"] else base / "data" / "exported_data.json"
        if not path.is_file():
            self.stderr.write(self.style.ERROR(f"文件不存在: {path}"))
            return

        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            self.stderr.write(self.style.ERROR("JSON 须为 Django dumpdata 的对象数组"))
            return

        skipped = 0
        kept = []
        for item in raw:
            model = item.get("model", "")
            if model.startswith("token_blacklist."):
                skipped += 1
                continue
            kept.append(item)

        if skipped:
            self.stdout.write(f"已跳过 {skipped} 条 token_blacklist 记录。")

        payload = json.dumps(kept)
        count = 0
        with transaction.atomic():
            for obj in serializers.deserialize("json", payload, ignorenonexistent=True):
                obj.save()
                count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"已导入 {count} 条记录。若上传的图片/文件不显示，请将旧环境的 media 目录同步到 MEDIA_ROOT。"
            )
        )
