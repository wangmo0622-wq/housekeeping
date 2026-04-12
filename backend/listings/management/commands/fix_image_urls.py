from django.core.management.base import BaseCommand
from urllib.parse import urlparse

from listings.models import Listing


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
    help = '修复数据库中的图片URL，移除域名前缀'

    def handle(self, *args, **options):
        self.stdout.write('开始修复图片URL...')
        
        count = 0
        listings = Listing.objects.all()
        
        for listing in listings:
            updated = False
            
            # 修复 cover_url
            if listing.cover_url:
                normalized_url = normalize_media_url(listing.cover_url)
                if normalized_url != listing.cover_url:
                    listing.cover_url = normalized_url
                    updated = True
            
            # 修复 cover_urls
            if listing.cover_urls and len(listing.cover_urls) > 0:
                normalized_urls = [normalize_media_url(u) for u in listing.cover_urls]
                if normalized_urls != listing.cover_urls:
                    listing.cover_urls = normalized_urls
                    updated = True
            
            if updated:
                listing.save(update_fields=['cover_url', 'cover_urls'])
                count += 1
                self.stdout.write(f'修复 Listing {listing.id}')
        
        self.stdout.write(self.style.SUCCESS(f'修复完成！共更新 {count} 条记录'))
