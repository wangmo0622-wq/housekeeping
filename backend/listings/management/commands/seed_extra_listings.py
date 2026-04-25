"""
向数据库增加若干条「服务管理」用的已发布上架记录（Listing + 审核通过记录）。
需在库中已有：至少一名认证通过的技师、若干启用中的分类。
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import TechnicianProfile
from catalog.models import Category
from listings.models import Listing, ListingAudit


# 6 条演示文案（标题、描述、价格、单位、服务区域）
SEEDS = [
    (
        "深度全屋保洁",
        "含客厅、卧室、厨房、卫生间等区域除尘拖地、台面擦拭、垃圾清理；可按面积沟通加项。",
        Decimal("268.00"),
        "元起",
        "章贡区,南康区",
    ),
    (
        "新生儿护理与产妇陪护",
        "协助产妇起居、新生儿喂养与基础护理观察，按天/按次预约，需提前沟通档期。",
        Decimal("380.00"),
        "元/天起",
        "章贡区,赣县区",
    ),
    (
        "老人白天居家陪护",
        "陪伴照料、简单家务、用药提醒与外出陪同（不含医疗处置），服务时间可议。",
        Decimal("200.00"),
        "元起",
        "章贡区",
    ),
    (
        "油烟机高温拆洗",
        "拆洗风轮蜗壳、清洁油路，现场防护与试机验收，具体以机型为准。",
        Decimal("158.00"),
        "元/台起",
        "全市可约",
    ),
    (
        "搬家打包与还原整理",
        "分类打包、标签管理、新居拆箱与基础归位，大件搬运需另议。",
        Decimal("500.00"),
        "元起",
        "章贡区,南康区,赣县区",
    ),
    (
        "家常钟点烹饪",
        "按次上门备菜与烹饪，口味与忌口提前说明；食材可由雇主自备或代购另议。",
        Decimal("88.00"),
        "元/次起",
        "章贡区,南康区",
    ),
]


class Command(BaseCommand):
    help = "新增 6 条已发布的服务上架（需已有已通过技师与启用分类）"

    def handle(self, *args, **options):
        techs = list(
            TechnicianProfile.objects.filter(
                verification_status=TechnicianProfile.VerificationStatus.APPROVED,
                is_disabled=False,
            ).order_by("id")
        )
        if not techs:
            self.stderr.write(self.style.ERROR("没有可用的「认证通过」技师，请先导入或配置技师资料。"))
            return

        # 二级分类：parent_id=0 为一级，非 0 为二级（见 catalog.Category）
        cats = list(
            Category.objects.filter(status=Category.Status.ENABLED)
            .exclude(parent_id=0)
            .order_by("id")[:24]
        )
        if not cats:
            self.stderr.write(self.style.ERROR("没有二级分类（parent_id≠0），请先维护分类数据。"))
            return
        # 若不足 6 个分类则循环使用
        while len(cats) < 6:
            cats = cats + cats
        cats = cats[:6]

        User = get_user_model()
        auditor = User.objects.filter(is_staff=True).first()

        now = timezone.now()
        created = 0
        for i, (title, desc, price, unit, areas) in enumerate(SEEDS):
            tech = techs[i % len(techs)]
            cat = cats[i]
            listing = Listing.objects.create(
                technician=tech,
                category=cat,
                title=title,
                description=desc,
                cover_url="",
                cover_urls=[],
                listing_price=price,
                listing_price_unit=unit,
                service_areas=areas,
                contact_info=tech.phone or "",
                status=Listing.Status.PUBLISHED,
                audit_note="",
                audited_by=auditor,
                reviewed_at=now,
                published_at=now,
            )
            ListingAudit.objects.create(
                listing=listing,
                status=ListingAudit.Status.PUBLISHED,
                audit_note="",
                reviewed_at=now,
                reviewed_by=auditor,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"已新增 {created} 条已发布服务（Listing）。"))
