"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import FileResponse
from django.shortcuts import render
import os

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from config.health import HealthCheckView

def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)

handler404 = page_not_found

# Swagger 配置
schema_view = get_schema_view(
   openapi.Info(
      title="家政服务 API",
      default_version='v1',
      description="家政服务后端 API 文档",
      terms_of_service="https://www.example.com/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def serve_favicon(request):
    favicon_path = os.path.join(settings.BASE_DIR, 'favicon.ico')
    return FileResponse(open(favicon_path, 'rb'), content_type='image/x-icon')

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    # 自定义管理后台（Admin Plus 风格）
    path('admin/', include('admin_portal.web_urls')),
    # Public / App / Admin APIs
    path('api/accounts/', include('accounts.urls')),
    path('api/public/', include('listings.public_urls')),
    path('api/tech/', include('listings.tech_urls')),
    path('api/admin/', include('admin_portal.urls')),
    # Favicon
    path('favicon.ico', serve_favicon),
]

if settings.ENABLE_API_DOCS:
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
