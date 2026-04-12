from django.core.management.base import BaseCommand
from urllib.parse import urlparse

from catalog.models import Banner, HotService


def normalize_media_url(url: str) -> str:
    """规范化媒体URL，移除域名前缀，只保留相对路径"""
    if not url:
        return url
    url = str(url).strip()
    if url.startswith(('http://', 'https://')):
        parsed = urlparse(url)
        url = parsed.path
    return url


class Command(BaseCommand):
    help = '修复catalog模块中的图片URL，移除域名前缀'

    def handle(self, *args, **options):
        self.stdout.write('开始修复catalog模块图片URL...')
        
        count = 0
        
        # 修复 Banner
        banners = Banner.objects.all()
        for banner in banners:
            updated = False
            
            # Banner 的 image 是 ImageField，由Django自动管理，但 image_url 可能需要修复
            if banner.image_url:
                normalized_url = normalize_media_url(banner.image_url)
                if normalized_url != banner.image_url:
                    banner.image_url = normalized_url
                    updated = True
            
            if updated:
                banner.save(update_fields=['image_url'])
                count += 1
                self.stdout.write(f'修复 Banner {banner.id}')
        
        # 修复 HotService
        hot_services = HotService.objects.all()
        for hot_service in hot_services:
            # HotService 的 icon 是 ImageField，由Django自动管理
            pass
        
        self.stdout.write(self.style.SUCCESS(f'修复完成！共更新 {count} 条记录'))
