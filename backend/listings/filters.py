import django_filters
from django.db.models import Q

from listings.models import Listing
from catalog.utils import get_ancestor_or_descendant_ids

class ListingFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label="搜索")
    q = django_filters.CharFilter(method='filter_search', label="搜索(别名)")
    category_id = django_filters.NumberFilter(method='filter_category_id', label="分类ID")
    service_type_id = django_filters.NumberFilter(field_name='services__id', distinct=True, label="服务类型ID")
    min_price = django_filters.NumberFilter(field_name='services__base_price', lookup_expr='gte', distinct=True, label="最低价格")
    max_price = django_filters.NumberFilter(field_name='services__base_price', lookup_expr='lte', distinct=True, label="最高价格")
    technician_id = django_filters.NumberFilter(field_name='technician_id', label="技师ID")

    class Meta:
        model = Listing
        fields = ['category_id', 'service_type_id', 'technician_id']

    def filter_search(self, queryset, name, value):
        if value:
            value = value.strip()
            return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))
        return queryset

    def filter_category_id(self, queryset, name, value):
        if value:
            related_category_ids = get_ancestor_or_descendant_ids(int(value))
            return queryset.filter(category_id__in=related_category_ids)
        return queryset
