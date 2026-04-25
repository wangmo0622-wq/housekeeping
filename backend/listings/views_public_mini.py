from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Banner, ServiceType, HotService
from catalog.utils import bootstrap_default_hot_services, get_ancestor_or_descendant_ids


class PublicBannerListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        banners = Banner.objects.filter(status=Banner.Status.ENABLED).order_by("sort_order", "-created_at")
        data = [
            {
                "id": b.id,
                "image_url": b.image.url if b.image else b.image_url,
                "link_type": b.link_type,
                "link_value": b.link_value,
                "title": b.title,
            }
            for b in banners
        ]
        return Response({"banners": data})


class PublicServiceTypeListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_id = request.query_params.get("category_id")
        service_types = ServiceType.objects.filter(status=ServiceType.Status.ENABLED)
        if category_id:
            try:
                related_ids = get_ancestor_or_descendant_ids(int(category_id))
            except (TypeError, ValueError):
                return Response({"detail": "分类ID不合法"}, status=status.HTTP_400_BAD_REQUEST)
            service_types = service_types.filter(category_id__in=related_ids)
        data = [
            {
                "id": st.id,
                "name": st.name,
                "category_id": st.category_id,
                "category_name": st.category.name,
                "base_price": str(st.base_price),
                "currency": st.currency,
                "price_unit": st.price_unit,
            }
            for st in service_types.select_related("category")
        ]
        return Response({"service_types": data})


class PublicCategoryServiceTypesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, category_id):
        related_ids = get_ancestor_or_descendant_ids(int(category_id))
        service_types = ServiceType.objects.filter(
            status=ServiceType.Status.ENABLED,
            category_id__in=related_ids
        ).select_related("category")
        data = [
            {
                "id": st.id,
                "name": st.name,
                "category_id": st.category_id,
                "category_name": st.category.name,
                "base_price": str(st.base_price),
                "currency": st.currency,
                "price_unit": st.price_unit,
            }
            for st in service_types
        ]
        return Response({"service_types": data})


class PublicHotServiceListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        bootstrap_default_hot_services()
        hot_services = HotService.objects.filter(status=HotService.Status.ENABLED).order_by("-sort_order", "-created_at")
        data = [
            {
                "id": hs.id,
                "name": hs.name,
                "icon": hs.icon.url if hs.icon else None,
                "link_type": hs.link_type,
                "link_value": hs.link_value,
            }
            for hs in hot_services
        ]
        return Response({"hot_services": data})
