from rest_framework import serializers
from urllib.parse import urlparse

from catalog.models import Category
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


def service_price_display(obj: Listing) -> str | None:
    """统一展示用价格文案：优先 listing 标价，否则取关联服务类型价格区间。"""
    if obj.listing_price is not None:
        u = (obj.listing_price_unit or "").strip()
        return f"{obj.listing_price} {u}".strip() if u else str(obj.listing_price)
    services = list(obj.services.all())
    if not services:
        return None
    prices = [s.base_price for s in services]
    lo, hi = min(prices), max(prices)
    ref = min(services, key=lambda s: (s.base_price, s.id))
    unit = (ref.price_unit or "次").strip()
    cur = (ref.currency or "CNY").strip()
    if lo == hi:
        return f"{lo} {cur}/{unit}"
    return f"{lo}～{hi} {cur}/{unit}"


def _normalize_cover_urls(cover_urls, cover_url_single: str) -> list[str]:
    """cover_urls 非 None 时表示完整替换列表；为 None 时仅用单张 cover_url。"""
    if cover_urls is not None:
        if not isinstance(cover_urls, list):
            raise serializers.ValidationError("cover_urls 须为字符串数组")
        if len(cover_urls) > Listing.MAX_COVER_URLS:
            raise serializers.ValidationError(f"封面图最多 {Listing.MAX_COVER_URLS} 张")
        return [normalize_media_url(str(u).strip()) for u in cover_urls if u and str(u).strip()][
            : Listing.MAX_COVER_URLS
        ]
    single = normalize_media_url((cover_url_single or "").strip())
    return [single] if single else []


def _listing_category_payload(obj: Listing) -> dict:
    """
    稳定分类展示口径：
    - category_id/category_name 表示一级分类
    - secondary_* 从关联 service_type 的 category 聚合（按 id 升序）
    """
    cat = obj.category
    if cat is None:
        return {
            "category_path": "",
            "primary_category_id": None,
            "primary_category_name": None,
            "secondary_category_id": None,
            "secondary_category_name": None,
            "secondary_categories": [],
        }

    if cat.parent_id == 0:
        primary = cat
    else:
        primary = Category.objects.filter(pk=cat.parent_id).only("id", "name", "parent_id").first()
        if primary is None or primary.parent_id != 0:
            primary = cat

    sec_map: dict[int, str] = {}
    # 若 listing.category 本身是二级，优先纳入展示
    if cat.parent_id == primary.id:
        sec_map[cat.id] = cat.name
    for s in obj.services.all():
        c = s.category
        if c and c.parent_id == primary.id:
            sec_map[c.id] = c.name

    secondary_categories = [
        {"id": sid, "name": sec_map[sid]} for sid in sorted(sec_map.keys())
    ]
    secondary_first = secondary_categories[0] if secondary_categories else None
    if secondary_first:
        category_path = f"{primary.name} > {secondary_first['name']}"
    else:
        category_path = primary.name

    return {
        "category_path": category_path,
        "primary_category_id": primary.id,
        "primary_category_name": primary.name,
        "secondary_category_id": secondary_first["id"] if secondary_first else None,
        "secondary_category_name": secondary_first["name"] if secondary_first else None,
        "secondary_categories": secondary_categories,
    }


def listing_category_payload(obj: Listing) -> dict:
    """对外暴露稳定分类展示口径。"""
    return _listing_category_payload(obj)


def filter_category_id_for_listing(obj: Listing) -> int | None:
    """
    推荐给小程序用于 GET /api/public/listings?category_id= 的值：
    有二级分类时与 secondary_category_id 一致，否则为一级 id。
    （JSON 里的 category_id 始终为一级，与历史字段兼容；仅用 category_id 筛选会偏「整棵一级树」。）
    """
    p = _listing_category_payload(obj)
    return p["secondary_category_id"] or p["primary_category_id"]


class ListingListSerializer(serializers.ModelSerializer):
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    category_path = serializers.SerializerMethodField()
    primary_category_id = serializers.SerializerMethodField()
    primary_category_name = serializers.SerializerMethodField()
    secondary_category_id = serializers.SerializerMethodField()
    secondary_category_name = serializers.SerializerMethodField()
    secondary_categories = serializers.SerializerMethodField()
    filter_category_id = serializers.SerializerMethodField()
    technician_name = serializers.CharField(source="technician.real_name", default="")
    services = serializers.SerializerMethodField()
    cover_urls = serializers.SerializerMethodField()
    listing_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, read_only=True)
    listing_price_unit = serializers.CharField(read_only=True)
    service_price = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "category_id",
            "category_name",
            "category_path",
            "primary_category_id",
            "primary_category_name",
            "secondary_category_id",
            "secondary_category_name",
            "secondary_categories",
            "filter_category_id",
            "cover_url",
            "cover_urls",
            "description",
            "technician_name",
            "listing_price",
            "listing_price_unit",
            "service_price",
            "services",
            "service_areas",
            "contact_info",
        ]

    def get_service_price(self, obj: Listing) -> str | None:
        return service_price_display(obj)

    def get_category_id(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_id"]

    def get_category_name(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_name"]

    def get_category_path(self, obj: Listing):
        return _listing_category_payload(obj)["category_path"]

    def get_primary_category_id(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_id"]

    def get_primary_category_name(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_name"]

    def get_secondary_category_id(self, obj: Listing):
        return _listing_category_payload(obj)["secondary_category_id"]

    def get_secondary_category_name(self, obj: Listing):
        return _listing_category_payload(obj)["secondary_category_name"]

    def get_secondary_categories(self, obj: Listing):
        return _listing_category_payload(obj)["secondary_categories"]

    def get_filter_category_id(self, obj: Listing) -> int | None:
        return filter_category_id_for_listing(obj)

    def get_cover_urls(self, obj: Listing) -> list[str]:
        if obj.cover_urls:
            return [normalize_media_url(u) for u in list(obj.cover_urls)[: Listing.MAX_COVER_URLS]]
        return [normalize_media_url(obj.cover_url)] if obj.cover_url else []

    def get_services(self, obj: Listing):
        services = list(obj.services.all())
        return [
            {
                "id": s.id,
                "name": s.name,
                "base_price": str(s.base_price),
                "currency": s.currency,
                "price_unit": s.price_unit,
            }
            for s in services
        ]


class ListingDetailSerializer(serializers.ModelSerializer):
    category_path = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    primary_category_id = serializers.SerializerMethodField()
    primary_category_name = serializers.SerializerMethodField()
    secondary_category_id = serializers.SerializerMethodField()
    secondary_category_name = serializers.SerializerMethodField()
    secondary_categories = serializers.SerializerMethodField()
    filter_category_id = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    cover_urls = serializers.SerializerMethodField()
    listing_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, read_only=True)
    listing_price_unit = serializers.CharField(read_only=True)
    service_price = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "cover_url",
            "cover_urls",
            "category_id",
            "category_name",
            "category_path",
            "primary_category_id",
            "primary_category_name",
            "secondary_category_id",
            "secondary_category_name",
            "secondary_categories",
            "filter_category_id",
            "technician_name",
            "phone",
            "listing_price",
            "listing_price_unit",
            "service_price",
            "services",
            "service_areas",
        ]

    def get_service_price(self, obj: Listing) -> str | None:
        return service_price_display(obj)

    def get_cover_urls(self, obj: Listing) -> list[str]:
        if obj.cover_urls:
            return [normalize_media_url(u) for u in list(obj.cover_urls)[: Listing.MAX_COVER_URLS]]
        return [normalize_media_url(obj.cover_url)] if obj.cover_url else []

    def get_category_path(self, obj: Listing) -> str:
        return _listing_category_payload(obj)["category_path"]

    def get_category_id(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_id"]

    def get_category_name(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_name"]

    def get_primary_category_id(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_id"]

    def get_primary_category_name(self, obj: Listing):
        return _listing_category_payload(obj)["primary_category_name"]

    def get_secondary_category_id(self, obj: Listing):
        return _listing_category_payload(obj)["secondary_category_id"]

    def get_secondary_category_name(self, obj: Listing):
        return _listing_category_payload(obj)["secondary_category_name"]

    def get_secondary_categories(self, obj: Listing):
        return _listing_category_payload(obj)["secondary_categories"]

    def get_filter_category_id(self, obj: Listing) -> int | None:
        return filter_category_id_for_listing(obj)

    technician_name = serializers.CharField(source="technician.real_name", default="")
    phone = serializers.CharField(source="technician.phone")

    def get_services(self, obj: Listing):
        services = list(obj.services.all())
        return [
            {
                "id": s.id,
                "name": s.name,
                "base_price": str(s.base_price),
                "currency": s.currency,
                "price_unit": s.price_unit,
                "tags": [t.name for t in s.tags.all()],
            }
            for s in services
        ]


class CallAttemptCreateSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    idempotency_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source = serializers.CharField(required=False, allow_blank=True, default="mini_program")


class ListingCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    secondary_category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    cover_urls = serializers.ListField(
        child=serializers.CharField(max_length=512),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    listing_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    listing_price_unit = serializers.CharField(max_length=16, required=False, allow_blank=True, default="次")
    service_areas = serializers.CharField(max_length=512, required=False, allow_blank=True, default="")
    contact_info = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")

    class Meta:
        model = Listing
        fields = [
            "title",
            "category_id",
            "secondary_category_id",
            "description",
            "cover_url",
            "cover_urls",
            "listing_price",
            "listing_price_unit",
            "service_areas",
            "contact_info",
        ]

    def validate(self, attrs):
        urls = _normalize_cover_urls(attrs.get("cover_urls"), attrs.get("cover_url") or "")
        attrs["cover_urls"] = urls
        attrs["cover_url"] = urls[0] if urls else ""
        category_id = attrs.get("category_id")
        category = Category.objects.filter(id=category_id).first()
        if not category:
            raise serializers.ValidationError("分类ID无效")
        if category.parent_id != 0:
            raise serializers.ValidationError("category_id 必须为一级分类")

        secondary_category_id = attrs.get("secondary_category_id")
        if secondary_category_id not in [None, ""]:
            sec = Category.objects.filter(id=secondary_category_id).first()
            if not sec:
                raise serializers.ValidationError("secondary_category_id 无效")
            if sec.parent_id != category.id:
                raise serializers.ValidationError("secondary_category_id 必须属于所选一级分类")
            # 统一落库到 Listing.category（存二级，便于稳定展示与筛选）
            attrs["category_id"] = sec.id
        return attrs


class ListingUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False)
    secondary_category_id = serializers.IntegerField(required=False, allow_null=True)
    cover_urls = serializers.ListField(
        child=serializers.CharField(max_length=512),
        required=False,
        allow_empty=True,
    )
    listing_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    listing_price_unit = serializers.CharField(max_length=16, required=False, allow_blank=True)
    service_areas = serializers.CharField(max_length=512, required=False, allow_blank=True)
    contact_info = serializers.CharField(max_length=128, required=False, allow_blank=True)

    class Meta:
        model = Listing
        fields = [
            "title",
            "category_id",
            "secondary_category_id",
            "description",
            "cover_url",
            "cover_urls",
            "listing_price",
            "listing_price_unit",
            "service_areas",
            "contact_info",
        ]

    def validate(self, attrs):
        inst = self.instance
        if "cover_urls" in attrs:
            attrs["cover_urls"] = _normalize_cover_urls(attrs["cover_urls"], "")
            attrs["cover_url"] = attrs["cover_urls"][0] if attrs["cover_urls"] else ""
        elif "cover_url" in attrs:
            single = attrs.get("cover_url")
            if single is None and inst:
                single = inst.cover_url
            attrs["cover_urls"] = _normalize_cover_urls(None, single or "")
            attrs["cover_url"] = attrs["cover_urls"][0] if attrs["cover_urls"] else ""

        if "category_id" not in attrs:
            raise serializers.ValidationError("更新时必须传 category_id（一级分类）")
        category_id = attrs.get("category_id")
        category = Category.objects.filter(id=category_id).first()
        if not category:
            raise serializers.ValidationError("分类ID无效")
        if category.parent_id != 0:
            raise serializers.ValidationError("category_id 必须为一级分类")

        secondary_category_id = attrs.get("secondary_category_id", None)
        if secondary_category_id not in [None, ""]:
            sec = Category.objects.filter(id=secondary_category_id).first()
            if not sec:
                raise serializers.ValidationError("secondary_category_id 无效")
            if sec.parent_id != category.id:
                raise serializers.ValidationError("secondary_category_id 必须属于所选一级分类")
            attrs["category_id"] = sec.id
        return attrs
