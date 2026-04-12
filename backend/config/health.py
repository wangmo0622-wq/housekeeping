"""容器与负载均衡探活。"""

from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """GET /health/ — 不鉴权；校验数据库连接。"""

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return JsonResponse({"status": "ok", "database": "up"})
        except Exception as exc:
            return JsonResponse({"status": "error", "database": str(exc)}, status=503)
