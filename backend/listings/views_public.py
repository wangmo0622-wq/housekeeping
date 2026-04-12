from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.cache import cache
from django.utils.cache import add_never_cache_headers, patch_response_headers
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import TechnicianProfile
from catalog.cache_keys import PUBLIC_CATEGORY_TREE_PAYLOAD_KEY
from catalog.models import Category
from catalog.utils import category_queryset_to_tree, get_ancestor_or_descendant_ids
from listings.models import Listing
from listings.serializers import (
    CallAttemptCreateSerializer,
    ListingDetailSerializer,
    ListingListSerializer,
)
from listings.utils import generate_qr_code
from monitoring.models import CallAttempt


class PublicCategoryTreeView(APIView):
    """GET /api/public/categories/tree — 仅启用分类，{ tree: [ { id, name, sort_order, children } ] }。"""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        secs = int(getattr(settings, "PUBLIC_CATEGORY_TREE_CACHE_SECONDS", 300))
        if secs > 0:
            cached = cache.get(PUBLIC_CATEGORY_TREE_PAYLOAD_KEY)
            if cached is not None:
                resp = Response(cached)
                patch_response_headers(resp, secs)
                return resp

        qs = Category.objects.filter(status=Category.Status.ENABLED).only(
            "id", "name", "parent_id", "sort_order"
        )
        payload = {"tree": category_queryset_to_tree(qs)}
        if secs > 0:
            cache.set(PUBLIC_CATEGORY_TREE_PAYLOAD_KEY, payload, secs)

        resp = Response(payload)
        if secs > 0:
            patch_response_headers(resp, secs)
        else:
            add_never_cache_headers(resp)
        return resp


class PublicListingsView(APIView):
    permission_classes = [permissions.AllowAny]

    class _Paginator(PageNumberPagination):
        page_size_query_param = "page_size"

    def get(self, request):
        search = (request.query_params.get("search") or request.query_params.get("q") or "").strip()
        category_id = request.query_params.get("category_id")
        service_type_id = request.query_params.get("service_type_id")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        ordering = request.query_params.get("ordering", "-published_at")
        technician_id = request.query_params.get("technician_id")

        qs = (
            Listing.objects.filter(status=Listing.Status.PUBLISHED, is_deleted=False)
            .select_related("category", "technician", "technician__user")
            .prefetch_related("services", "services__tags")
            .filter(technician__verification_status=TechnicianProfile.VerificationStatus.APPROVED)
            .filter(technician__is_disabled=False)
        )

        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        # 处理 technician_id 参数
        if technician_id:
            try:
                technician_id_int = int(technician_id)
                qs = qs.filter(technician_id=technician_id_int)
            except ValueError:
                return Response({"detail": "技师ID不合法"}, status=status.HTTP_400_BAD_REQUEST)

        if category_id:
            try:
                category_id_int = int(category_id)
            except ValueError:
                return Response({"detail": "分类ID不合法"}, status=status.HTTP_400_BAD_REQUEST)
            related_category_ids = get_ancestor_or_descendant_ids(category_id_int)
            qs = qs.filter(category_id__in=related_category_ids)

        if service_type_id:
            try:
                service_type_id_int = int(service_type_id)
                qs = qs.filter(services__id=service_type_id_int).distinct()
            except ValueError:
                return Response({"detail": "服务类型ID不合法"}, status=status.HTTP_400_BAD_REQUEST)

        if min_price:
            try:
                min_price_float = float(min_price)
                qs = qs.filter(services__base_price__gte=min_price_float).distinct()
            except ValueError:
                return Response({"detail": "最低价格格式不合法"}, status=status.HTTP_400_BAD_REQUEST)

        if max_price:
            try:
                max_price_float = float(max_price)
                qs = qs.filter(services__base_price__lte=max_price_float).distinct()
            except ValueError:
                return Response({"detail": "最高价格格式不合法"}, status=status.HTTP_400_BAD_REQUEST)

        valid_orderings = ["-published_at", "-created_at", "published_at", "created_at"]
        if ordering in valid_orderings:
            qs = qs.order_by(ordering, "-created_at")
        else:
            qs = qs.order_by("-published_at", "-created_at")

        paginator = self._Paginator()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ListingListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PublicListingDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, listing_id: int):
        listing = (
            Listing.objects.select_related("category", "technician", "technician__user").prefetch_related(
                "services", "services__tags"
            )
            .filter(id=listing_id, is_deleted=False)
            .first()
        )
        if not listing:
            raise Http404

        # 严格门禁：不满足就 404
        is_visible = (
            listing.status == Listing.Status.PUBLISHED
            and listing.technician.verification_status == TechnicianProfile.VerificationStatus.APPROVED
            and not listing.technician.is_disabled
        )
        if not is_visible:
            raise Http404

        serializer = ListingDetailSerializer(listing)
        return Response(serializer.data)


class PublicCallAttemptCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CallAttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing_id = serializer.validated_data["listing_id"]
        idempotency_key = serializer.validated_data.get("idempotency_key") or ""
        source = serializer.validated_data.get("source") or "mini_program"

        listing = get_object_or_404(
            Listing.objects.select_related("technician", "technician__user", "category"),
            id=listing_id,
            is_deleted=False,
        )

        # 门禁校验：必须是可见详情
        if not (
            listing.status == Listing.Status.PUBLISHED
            and listing.technician.verification_status == TechnicianProfile.VerificationStatus.APPROVED
            and not listing.technician.is_disabled
        ):
            raise Http404

        CallAttempt.objects.create(
            user=request.user,
            technician=listing.technician,
            listing=listing,
            source=source,
            idempotency_key=idempotency_key[:128],
        )

        return Response({"ok": True}, status=status.HTTP_201_CREATED)


class PublicTechniciansView(APIView):
    permission_classes = [permissions.AllowAny]

    class _Paginator(PageNumberPagination):
        page_size_query_param = "page_size"

    def _get_technician_data(self, profile):
        """
        生成技师数据，包括二维码
        """
        qr_content = f"/pages/technician-detail/technician-detail?id={profile.id}"
        qr_data_url = generate_qr_code(qr_content)
        
        return {
            "id": profile.id,
            "real_name": profile.real_name,
            "phone": profile.phone,
            "bio": profile.bio,
            "service_types": profile.service_types,
            "work_years": profile.work_years,
            "gender": profile.gender,
            "avatar": profile.avatar.url if profile.avatar else None,
            "is_recommended": profile.is_recommended,
            "recommended_at": profile.recommended_at.isoformat() if profile.recommended_at else None,
            "updated_at": profile.updated_at.isoformat(),
            "qrcode": qr_data_url
        }

    def get(self, request):
        # 获取推荐技师，按推荐时间倒序，最后推荐的越靠前
        queryset = TechnicianProfile.objects.filter(
            verification_status=TechnicianProfile.VerificationStatus.APPROVED,
            is_disabled=False
        )
        
        # 处理 is_recommended 参数
        is_recommended = request.query_params.get('is_recommended')
        if is_recommended == 'true':
            queryset = queryset.filter(is_recommended=True)

        kw = (request.query_params.get("search") or request.query_params.get("q") or "").strip()
        if kw:
            queryset = queryset.filter(
                Q(real_name__icontains=kw)
                | Q(service_types__icontains=kw)
                | Q(bio__icontains=kw)
            )

        queryset = queryset.order_by(
            "-is_recommended",  # 推荐的排在前面
            "-recommended_at",  # 推荐时间倒序
            "-updated_at"  # 最后更新时间
        )

        paginator = self._Paginator()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            items = [self._get_technician_data(profile) for profile in page]
            return paginator.get_paginated_response(items)

        # 未分页的情况
        items = [self._get_technician_data(profile) for profile in queryset]
        return Response(items)


class PublicTechnicianDetailView(APIView):
    """GET /api/public/technicians/<id> — 获取技师详情（用于二维码扫描）。"""

    permission_classes = [permissions.AllowAny]

    def get(self, request, technician_id):
        # 获取技师资料，只返回已审核通过且未禁用的技师
        profile = get_object_or_404(
            TechnicianProfile,
            id=technician_id,
            verification_status=TechnicianProfile.VerificationStatus.APPROVED,
            is_disabled=False
        )

        # 获取技师的服务列表，只返回已发布且未删除的服务
        listings = Listing.objects.filter(
            technician=profile,
            status=Listing.Status.PUBLISHED,
            is_deleted=False
        ).order_by("-published_at")

        # 生成二维码
        qr_content = f"/pages/technician-detail/technician-detail?id={profile.id}"
        qr_data_url = generate_qr_code(qr_content)

        # 序列化技师信息
        technician_data = {
            "id": profile.id,
            "real_name": profile.real_name,
            "phone": profile.phone,
            "bio": profile.bio,
            "service_types": profile.service_types,
            "work_years": profile.work_years,
            "gender": profile.gender,
            "avatar": profile.avatar.url if profile.avatar else None,
            "is_recommended": profile.is_recommended,
            "updated_at": profile.updated_at.isoformat(),
            "qrcode": qr_data_url
        }

        # 序列化服务列表
        services_data = []
        for listing in listings:
            services_data.append({
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "cover_url": listing.cover_url,
                "service_areas": listing.service_areas,
                "contact_info": listing.contact_info,
                "published_at": listing.published_at.isoformat() if listing.published_at else None
            })

        return Response({
            "technician": technician_data,
            "services": services_data
        })

