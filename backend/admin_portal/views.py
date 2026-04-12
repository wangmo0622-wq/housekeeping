import base64
import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.http import Http404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import TechnicianProfile, TechnicianVerification
from admin_portal.captcha_utils import create_captcha, verify_captcha
from admin_portal.models import AdminMenu
from catalog.models import Banner, Category, HotService, ServiceType
from listings.models import Listing


def format_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


def captcha_refresh_view(request):
    captcha_id, image_buffer = create_captcha()
    image_base64 = base64.b64encode(image_buffer.getvalue()).decode("utf-8")
    return JsonResponse({"captcha_id": captcha_id, "image": f"data:image/png;base64,{image_base64}"})


class CaptchaTokenObtainPairView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        captcha_id = request.data.get("captcha_id")
        captcha_code = request.data.get("captcha_code")
        if not captcha_id or not captcha_code:
            return Response({"detail": "请输入验证码"}, status=status.HTTP_400_BAD_REQUEST)
        ok, msg = verify_captcha(captcha_id, captcha_code)
        if not ok:
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_staff:
            return Response({"detail": "您没有管理员权限"}, status=status.HTTP_403_FORBIDDEN)
        refresh = RefreshToken.for_user(user)
        refresh["is_staff"] = user.is_staff
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})


class AdminDashboardView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response(
            {
                "statistics": {
                    "total_users": User.objects.filter(is_staff=False).count(),
                    "total_technicians": TechnicianProfile.objects.count(),
                    "verified_technicians": TechnicianProfile.objects.filter(
                        verification_status=TechnicianProfile.VerificationStatus.APPROVED
                    ).count(),
                    "total_services": Listing.objects.filter(status=Listing.Status.PUBLISHED).count(),
                },
                "trends": {"months": [], "user_counts": [], "technician_counts": [], "service_counts": []},
            }
        )


class AdminOperatorCategoryTreeView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        items = Category.objects.all().order_by("parent_id", "sort_order", "id")
        return Response({"tree": [{"id": c.id, "name": c.name, "parent_id": c.parent_id, "status": c.status} for c in items]})


class AdminOperatorCategoryCRUDView(APIView):
    permission_classes = [IsOperator]

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "名称必填"}, status=status.HTTP_400_BAD_REQUEST)
        parent_id = int(request.data.get("parent_id") or 0)
        c = Category.objects.create(name=name, parent_id=parent_id, sort_order=int(request.data.get("sort_order") or 0))
        return Response({"ok": True, "id": c.id}, status=status.HTTP_201_CREATED)


class AdminOperatorCategoryDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, category_id: int):
        c = Category.objects.filter(id=category_id).first()
        if not c:
            raise Http404
        for f in ("name", "status"):
            if f in request.data:
                setattr(c, f, request.data[f])
        if "sort_order" in request.data:
            c.sort_order = int(request.data.get("sort_order") or 0)
        c.save()
        return Response({"ok": True})

    def delete(self, request, category_id: int):
        c = Category.objects.filter(id=category_id).first()
        if not c:
            raise Http404
        c.delete()
        return Response({"ok": True})


class AdminTechniciansView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        qs = TechnicianProfile.objects.select_related("user").order_by("-updated_at")
        items = [{"id": x.id, "real_name": x.real_name, "phone": x.phone, "verification_status": x.verification_status, "updated_at": format_dt(x.updated_at)} for x in qs[:200]]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})


class AdminTechnicianDetailView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, technician_id: int):
        p = TechnicianProfile.objects.filter(id=technician_id).first()
        if not p:
            raise Http404
        return Response({"id": p.id, "real_name": p.real_name, "phone": p.phone, "verification_status": p.verification_status})


class AdminTechnicianVerificationActionView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, technician_id: int, action: str):
        p = TechnicianProfile.objects.filter(id=technician_id).first()
        if not p:
            raise Http404
        if action == "approve":
            p.verification_status = TechnicianProfile.VerificationStatus.APPROVED
        elif action == "reject":
            p.verification_status = TechnicianProfile.VerificationStatus.REJECTED
        elif action == "disable":
            p.is_disabled = True
        elif action == "enable":
            p.is_disabled = False
        elif action == "recommend":
            p.is_recommended = not p.is_recommended
        p.save()
        return Response({"ok": True})


class AdminListingsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        qs = Listing.objects.select_related("technician", "category").order_by("-created_at")
        items = [{"id": x.id, "title": x.title, "status": x.status, "created_at": format_dt(x.created_at)} for x in qs[:200]]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})


class AdminListingDetailView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, listing_id: int):
        x = Listing.objects.filter(id=listing_id).first()
        if not x:
            raise Http404
        return Response({"id": x.id, "title": x.title, "description": x.description, "status": x.status})

    def delete(self, request, listing_id: int):
        x = Listing.objects.filter(id=listing_id).first()
        if not x:
            raise Http404
        x.is_deleted = True
        x.save()
        return Response({"ok": True})


class AdminListingAuditActionView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, listing_id: int, action: str):
        x = Listing.objects.filter(id=listing_id).first()
        if not x:
            raise Http404
        mapping = {"approve": Listing.Status.PUBLISHED, "reject": Listing.Status.REJECTED, "disable": Listing.Status.DISABLED, "enable": Listing.Status.PUBLISHED}
        if action in mapping:
            x.status = mapping[action]
            x.reviewed_at = timezone.now()
            x.audited_by = request.user
            x.save()
        return Response({"ok": True})


class AdminServiceTypesView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        qs = ServiceType.objects.select_related("category").order_by("-updated_at")
        items = [{"id": s.id, "name": s.name, "category_id": s.category_id, "status": s.status} for s in qs[:200]]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        category_id = request.data.get("category_id")
        base_price = request.data.get("base_price")
        if not name or not category_id or base_price in [None, ""]:
            return Response({"detail": "参数不完整"}, status=status.HTTP_400_BAD_REQUEST)
        s = ServiceType.objects.create(name=name, category_id=int(category_id), base_price=base_price)
        return Response({"ok": True, "id": s.id}, status=status.HTTP_201_CREATED)


class AdminServiceTypeDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, service_type_id: int):
        s = ServiceType.objects.filter(id=service_type_id).first()
        if not s:
            raise Http404
        for f in ("name", "status", "base_price"):
            if f in request.data:
                setattr(s, f, request.data[f])
        if "category_id" in request.data:
            s.category_id = int(request.data["category_id"])
        s.save()
        return Response({"ok": True})


class AdminRegisteredUsersView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        qs = User.objects.filter(is_staff=False).order_by("-date_joined")
        items = [{"id": u.id, "username": u.username, "is_active": u.is_active, "date_joined": str(u.date_joined)} for u in qs[:200]]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        password = request.data.get("password", "")
        if not phone or not password:
            return Response({"detail": "手机号和密码必填"}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r"^1[3-9]\d{9}$", phone):
            return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
        if not username:
            username = f"用户_{phone[-5:]}"
        if User.objects.filter(username=username).exists():
            return Response({"detail": "用户名已存在"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password, is_staff=False)
        TechnicianProfile.objects.create(user=user, phone=phone, verification_status="uninitiated")
        return Response({"ok": True, "id": user.id}, status=status.HTTP_201_CREATED)


class AdminRegisteredUserDetailView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, user_id: int):
        u = User.objects.filter(id=user_id, is_staff=False).first()
        if not u:
            raise Http404
        return Response({"id": u.id, "username": u.username, "is_active": u.is_active})

    def patch(self, request, user_id: int):
        u = User.objects.filter(id=user_id, is_staff=False).first()
        if not u:
            raise Http404
        if "is_active" in request.data:
            u.is_active = bool(request.data.get("is_active"))
            u.save(update_fields=["is_active"])
        return Response({"ok": True})


class AdminRegisteredUserResetPasswordView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, user_id: int):
        u = User.objects.filter(id=user_id, is_staff=False).first()
        if not u:
            raise Http404
        new_password = u.username[-6:] if u.username else "123456"
        u.set_password(new_password)
        u.save(update_fields=["password"])
        return Response({"ok": True, "new_password": new_password})


class AdminAdminUsersView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        qs = User.objects.filter(is_staff=True).order_by("-date_joined")
        items = [{"id": u.id, "username": u.username, "is_active": u.is_active, "is_superuser": u.is_superuser} for u in qs]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password", "")
        if not username or not password:
            return Response({"detail": "用户名和密码必填"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "用户名已存在"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"detail": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(
            username=username,
            password=password,
            email=(request.data.get("email") or "").strip(),
            first_name=(request.data.get("first_name") or "").strip(),
            is_staff=True,
            is_superuser=bool(request.data.get("is_superuser", False)),
        )
        return Response({"ok": True, "id": user.id}, status=status.HTTP_201_CREATED)


class AdminAdminUserDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, user_id: int):
        u = User.objects.filter(id=user_id, is_staff=True).first()
        if not u:
            raise Http404
        for f in ("first_name", "email"):
            if f in request.data:
                setattr(u, f, request.data[f])
        if "is_active" in request.data:
            u.is_active = bool(request.data["is_active"])
        if "is_superuser" in request.data:
            u.is_superuser = bool(request.data["is_superuser"])
        u.save()
        return Response({"ok": True})

    def delete(self, request, user_id: int):
        u = User.objects.filter(id=user_id, is_staff=True).first()
        if not u:
            raise Http404
        if u.id == request.user.id:
            return Response({"detail": "不能删除自己"}, status=status.HTTP_400_BAD_REQUEST)
        u.delete()
        return Response({"ok": True})


class AdminCurrentUserView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        u = request.user
        return Response({"id": u.id, "username": u.username, "email": u.email, "first_name": u.first_name, "avatar_url": u.username[:1].upper()})


class AdminChangePasswordView(APIView):
    permission_classes = [IsOperator]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")
        if not user.check_password(old_password):
            return Response({"detail": "旧密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({"detail": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"ok": True})


class AdminProfileView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        u = request.user
        return Response({"id": u.id, "username": u.username, "email": u.email, "first_name": u.first_name})

    def patch(self, request):
        u = request.user
        for f in ("first_name", "email"):
            if f in request.data:
                setattr(u, f, str(request.data.get(f)).strip())
        u.save()
        return Response({"ok": True})


class AdminBannersView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        qs = Banner.objects.all().order_by("sort_order", "-created_at")
        items = [{"id": x.id, "title": x.title, "image_url": x.image.url if x.image else x.image_url, "status": x.status} for x in qs]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})

    def post(self, request):
        b = Banner.objects.create(
            title=(request.data.get("title") or "").strip(),
            image=request.FILES.get("image"),
            image_url=(request.data.get("image_url") or "").strip(),
            link_type=request.data.get("link_type") or Banner.LinkType.NONE,
            link_value=(request.data.get("link_value") or "").strip(),
            sort_order=int(request.data.get("sort_order") or 0),
            status=request.data.get("status") or Banner.Status.ENABLED,
        )
        return Response({"ok": True, "id": b.id}, status=status.HTTP_201_CREATED)


class AdminBannerDetailView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, banner_id: int):
        b = Banner.objects.filter(id=banner_id).first()
        if not b:
            raise Http404
        for f in ("title", "image_url", "link_type", "link_value", "status"):
            if f in request.data:
                setattr(b, f, request.data.get(f))
        if "sort_order" in request.data:
            b.sort_order = int(request.data.get("sort_order") or 0)
        if request.FILES.get("image"):
            b.image = request.FILES.get("image")
        b.save()
        return Response({"ok": True})

    def delete(self, request, banner_id: int):
        b = Banner.objects.filter(id=banner_id).first()
        if not b:
            raise Http404
        b.delete()
        return Response({"ok": True})


class AdminHotServicesView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        qs = HotService.objects.all().order_by("-sort_order", "-created_at")
        items = [{"id": x.id, "name": x.name, "status": x.status, "link_type": x.link_type, "link_value": x.link_value} for x in qs]
        return Response({"items": items, "total": qs.count(), "page": 1, "page_size": 200, "total_pages": 1})

    def post(self, request):
        hs = HotService.objects.create(
            name=(request.data.get("name") or "").strip(),
            icon=request.FILES.get("icon"),
            link_type=request.data.get("link_type") or HotService.LinkType.NONE,
            link_value=(request.data.get("link_value") or "").strip(),
            sort_order=int(request.data.get("sort_order") or 0),
            status=request.data.get("status") or HotService.Status.ENABLED,
        )
        return Response({"ok": True, "id": hs.id}, status=status.HTTP_201_CREATED)


class AdminHotServiceDetailView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, hot_service_id: int):
        hs = HotService.objects.filter(id=hot_service_id).first()
        if not hs:
            raise Http404
        return Response({"id": hs.id, "name": hs.name, "status": hs.status, "link_type": hs.link_type, "link_value": hs.link_value})

    def patch(self, request, hot_service_id: int):
        hs = HotService.objects.filter(id=hot_service_id).first()
        if not hs:
            raise Http404
        for f in ("name", "link_type", "link_value", "status"):
            if f in request.data:
                setattr(hs, f, request.data.get(f))
        if "sort_order" in request.data:
            hs.sort_order = int(request.data.get("sort_order") or 0)
        if request.FILES.get("icon"):
            hs.icon = request.FILES.get("icon")
        hs.save()
        return Response({"ok": True})

    def delete(self, request, hot_service_id: int):
        hs = HotService.objects.filter(id=hot_service_id).first()
        if not hs:
            raise Http404
        hs.delete()
        return Response({"ok": True})


def _bootstrap_default_menus():
    # 仅在完全空表时初始化默认菜单，避免用户删除/调整后被自动“补回”
    if AdminMenu.objects.exists():
        return

    def get_or_create_by_key(key: str, defaults: dict):
        # 兼容历史脏数据：key 重复时取最早一条，避免 get_or_create 抛 MultipleObjectsReturned
        obj = AdminMenu.objects.filter(key=key).order_by("id").first()
        if obj:
            return obj
        return AdminMenu.objects.create(key=key, **defaults)

    section_business = get_or_create_by_key(
        "section_business",
        {"name": "业务管理", "is_section": True, "sort_order": 10},
    )
    section_user = get_or_create_by_key(
        "section_user",
        {"name": "用户管理", "is_section": True, "sort_order": 20},
    )
    section_account = get_or_create_by_key(
        "section_account",
        {"name": "账号设置", "is_section": True, "sort_order": 30},
    )

    defaults = [
        {"name": "系统首页", "key": "dashboard", "path": "/admin/dashboard/", "sort_order": 1, "parent": None},
        {"name": "分类管理", "key": "categories", "path": "/admin/categories/", "sort_order": 1, "parent": section_business},
        {"name": "服务管理", "key": "listings", "path": "/admin/listings/", "sort_order": 2, "parent": section_business},
        {"name": "技师认证", "key": "technicians", "path": "/admin/technicians/", "sort_order": 3, "parent": section_business},
        {"name": "轮播管理", "key": "banners", "path": "/admin/banners/", "sort_order": 4, "parent": section_business},
        {"name": "热门服务", "key": "hot_services", "path": "/admin/hot-services/", "sort_order": 5, "parent": section_business},
        {"name": "会员列表", "key": "registered_users", "path": "/admin/registered-users/", "sort_order": 1, "parent": section_user},
        {"name": "管理用户", "key": "admin_users", "path": "/admin/admin-users/", "sort_order": 2, "parent": section_user},
        {"name": "菜单管理", "key": "menus", "path": "/admin/menus/", "sort_order": 3, "parent": section_user},
        {"name": "修改密码", "key": "change_password", "path": "/admin/change-password/", "sort_order": 1, "parent": section_account},
        {"name": "个人资料", "key": "profile", "path": "/admin/profile/", "sort_order": 2, "parent": section_account},
    ]
    for item in defaults:
        get_or_create_by_key(
            item["key"],
            {
                "name": item["name"],
                "path": item["path"],
                "sort_order": item["sort_order"],
                "parent": item["parent"],
                "is_section": False,
            },
        )


class AdminMenusView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        _bootstrap_default_menus()
        manage_mode = request.query_params.get("manage") == "1"

        if manage_mode:
            qs = AdminMenu.objects.all().select_related("parent").prefetch_related("children").order_by("sort_order", "id")
        else:
            visible_qs = (
                AdminMenu.objects.filter(is_enabled=True, is_visible=True)
                .filter(Q(allow_all_staff=True) | Q(allowed_users=request.user))
                .distinct()
            )
            visible_ids = list(visible_qs.values_list("id", flat=True))
            parent_ids = list(visible_qs.exclude(parent_id__isnull=True).values_list("parent_id", flat=True))
            qs = (
                AdminMenu.objects.filter(Q(id__in=visible_ids) | Q(id__in=parent_ids))
                .select_related("parent")
                .prefetch_related("children")
                .distinct()
                .order_by("sort_order", "id")
            )
        rows = list(qs)
        by_parent = {}
        ids_set = {m.id for m in rows}
        for m in rows:
            # 父节点不在当前结果集时，提升为根节点，避免一级菜单“消失”
            pid = m.parent_id if (m.parent_id and m.parent_id in ids_set) else 0
            by_parent.setdefault(pid, []).append(m)

        def to_payload(menu):
            return {
                "id": menu.id,
                "name": menu.name,
                "key": menu.key,
                "path": menu.path,
                "icon": menu.icon,
                "is_section": menu.is_section,
                "sort_order": menu.sort_order,
                "is_visible": menu.is_visible,
                "is_enabled": menu.is_enabled,
                "allow_all_staff": menu.allow_all_staff,
                "parent_id": menu.parent_id,
                "children": [to_payload(c) for c in by_parent.get(menu.id, [])],
            }

        root_items = [to_payload(m) for m in by_parent.get(0, [])]
        return Response({"items": root_items})

    def post(self, request):
        payload = request.data
        name = str(payload.get("name") or "").strip()
        if not name:
            return Response({"detail": "菜单名称必填"}, status=status.HTTP_400_BAD_REQUEST)

        parent_id = payload.get("parent_id")
        parent = None
        if parent_id not in [None, "", 0, "0"]:
            parent = AdminMenu.objects.filter(id=int(parent_id)).first()
            if not parent:
                return Response({"detail": "父菜单不存在"}, status=status.HTTP_400_BAD_REQUEST)

        m = AdminMenu.objects.create(
            name=name,
            key=str(payload.get("key") or "").strip(),
            path=str(payload.get("path") or "").strip(),
            icon=str(payload.get("icon") or "").strip(),
            parent=parent,
            is_section=bool(payload.get("is_section", False)),
            sort_order=int(payload.get("sort_order") or 0),
            is_visible=bool(payload.get("is_visible", True)),
            is_enabled=bool(payload.get("is_enabled", True)),
            allow_all_staff=bool(payload.get("allow_all_staff", True)),
        )
        return Response({"ok": True, "id": m.id}, status=status.HTTP_201_CREATED)


class AdminMenuDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, menu_id: int):
        m = AdminMenu.objects.filter(id=menu_id).first()
        if not m:
            raise Http404

        payload = request.data
        if "name" in payload:
            name = str(payload.get("name") or "").strip()
            if not name:
                return Response({"detail": "菜单名称不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            m.name = name
        if "key" in payload:
            m.key = str(payload.get("key") or "").strip()
        if "path" in payload:
            m.path = str(payload.get("path") or "").strip()
        if "icon" in payload:
            m.icon = str(payload.get("icon") or "").strip()
        if "sort_order" in payload:
            m.sort_order = int(payload.get("sort_order") or 0)
        if "is_section" in payload:
            m.is_section = bool(payload.get("is_section"))
        if "is_visible" in payload:
            m.is_visible = bool(payload.get("is_visible"))
        if "is_enabled" in payload:
            m.is_enabled = bool(payload.get("is_enabled"))
        if "allow_all_staff" in payload:
            m.allow_all_staff = bool(payload.get("allow_all_staff"))

        if "parent_id" in payload:
            parent_id = payload.get("parent_id")
            if parent_id in [None, "", 0, "0"]:
                m.parent = None
            else:
                parent = AdminMenu.objects.filter(id=int(parent_id)).first()
                if not parent:
                    return Response({"detail": "父菜单不存在"}, status=status.HTTP_400_BAD_REQUEST)
                if parent.id == m.id:
                    return Response({"detail": "父菜单不能是自己"}, status=status.HTTP_400_BAD_REQUEST)
                m.parent = parent

        m.save()
        return Response({"ok": True})

    def delete(self, request, menu_id: int):
        m = AdminMenu.objects.filter(id=menu_id).first()
        if not m:
            raise Http404
        if m.children.exists():
            return Response({"detail": "请先删除子菜单"}, status=status.HTTP_400_BAD_REQUEST)
        m.delete()
        return Response({"ok": True})
import re
from io import BytesIO
import base64
import qrcode
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone
from django.utils.dateformat import format as dt_format
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from accounts.models import TechnicianProfile, TechnicianVerification
from catalog.models import Category, ServiceType, Banner, HotService
from catalog.utils import (
    category_queryset_to_tree,
    get_descendant_ids,
    validate_category_parent_for_save,
)
from listings.models import Listing
from listings.serializers import listing_category_payload, service_price_display
from monitoring.models import AdminMonitoringCall


def format_dt(dt):
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _listing_cover_urls(listing: Listing) -> list:
    if listing.cover_urls:
        return list(listing.cover_urls)[: Listing.MAX_COVER_URLS]
    return [listing.cover_url] if listing.cover_url else []


class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminDashboardView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        # 统计数据
        total_users = User.objects.filter(is_staff=False).count()
        total_technicians = TechnicianProfile.objects.count()
        verified_technicians = TechnicianProfile.objects.filter(verification_status=TechnicianProfile.VerificationStatus.APPROVED).count()
        
        # 服务人次（这里使用发布的服务数量作为近似值）
        total_services = Listing.objects.filter(status=Listing.Status.PUBLISHED).count()
        
        # 12月趋势数据
        now = timezone.now()
        months = []
        user_counts = []
        technician_counts = []
        service_counts = []
        
        for i in range(11, -1, -1):
            target_month = now - timezone.timedelta(days=i*30)
            month_start = target_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timezone.timedelta(days=31)).replace(day=1)
            
            # 用户注册数
            month_users = User.objects.filter(is_staff=False, date_joined__gte=month_start, date_joined__lt=month_end).count()
            
            # 技师认证数
            month_technicians = TechnicianProfile.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            
            # 服务发布数
            month_services = Listing.objects.filter(status=Listing.Status.PUBLISHED, published_at__gte=month_start, published_at__lt=month_end).count()
            
            months.append(month_start.strftime('%Y-%m'))
            user_counts.append(month_users)
            technician_counts.append(month_technicians)
            service_counts.append(month_services)
        
        return Response({
            "statistics": {
                "total_users": total_users,
                "total_technicians": total_technicians,
                "verified_technicians": verified_technicians,
                "total_services": total_services
            },
            "trends": {
                "months": months,
                "user_counts": user_counts,
                "technician_counts": technician_counts,
                "service_counts": service_counts
            }
        })


def build_category_tree():
    """管理端全部分类树，节点含 status。"""
    qs = Category.objects.only("id", "name", "parent_id", "sort_order", "status")
    # 管理端只展示/编辑两级：一级根（depth=1）+ 二级子类（depth=2）
    return category_queryset_to_tree(qs, include_status=True, max_depth=2)


class AdminOperatorCategoryTreeView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response({"tree": build_category_tree()})


class AdminOperatorCategoryCRUDView(APIView):
    permission_classes = [IsOperator]

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "名称必填"}, status=status.HTTP_400_BAD_REQUEST)

        parent_id = request.data.get("parent_id")
        parent = None
        if parent_id:
            parent = Category.objects.filter(id=parent_id).first()
            if not parent:
                return Response({"detail": "父级分类不存在"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_category_parent_for_save(parent=parent, node=None)
        except ValidationError as e:
            return Response(
                {"detail": e.messages[0] if e.messages else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pid = parent.pk if parent else 0
        c = Category.objects.create(
            name=name,
            parent_id=pid,
            sort_order=int(request.data.get("sort_order") or 0),
            status=Category.Status.ENABLED,
        )
        return Response({"ok": True, "id": c.id}, status=status.HTTP_201_CREATED)


class AdminOperatorCategoryDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, category_id: int):
        c = Category.objects.filter(id=category_id).first()
        if not c:
            raise Http404

        name = request.data.get("name")
        if name is not None:
            c.name = str(name).strip()

        status_val = request.data.get("status")
        if status_val in [Category.Status.ENABLED, Category.Status.DISABLED]:
            c.status = status_val

        if "sort_order" in request.data:
            c.sort_order = int(request.data.get("sort_order") or 0)

        if "parent_id" in request.data:
            parent_id = request.data.get("parent_id")
            if parent_id in [None, "", 0]:
                c.parent_id = 0
            else:
                parent = Category.objects.filter(id=parent_id).first()
                if not parent:
                    return Response({"detail": "父级分类不存在"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    validate_category_parent_for_save(parent=parent, node=c)
                except ValidationError as e:
                    return Response(
                        {"detail": e.messages[0] if e.messages else str(e)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                c.parent_id = parent.pk

        c.save()
        return Response({"ok": True})

    def delete(self, request, category_id: int):
        """删除分类，检查是否有关联的服务"""
        from listings.models import Listing
        from catalog.models import ServiceType
        
        c = Category.objects.filter(id=category_id).first()
        if not c:
            raise Http404

        # 检查是否有子分类
        children_count = Category.objects.filter(parent_id=c.id).count()
        if children_count > 0:
            return Response(
                {"detail": f"该分类下有 {children_count} 个子分类，请先删除子分类"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查是否有服务类型关联
        service_type_count = ServiceType.objects.filter(category=c).count()
        if service_type_count > 0:
            return Response(
                {"detail": f"该分类下有关联的 {service_type_count} 个服务类型，无法删除"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查是否有服务发布关联
        listing_count = Listing.objects.filter(category=c).count()
        if listing_count > 0:
            return Response(
                {"detail": f"该分类下有关联的 {listing_count} 条服务发布，无法删除"},
                status=status.HTTP_400_BAD_REQUEST
            )

        c.delete()
        return Response({"ok": True})


class AdminTechniciansView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        status_val = request.query_params.get("status")
        q = request.query_params.get("q", "").strip()
        name = request.query_params.get("name", "").strip()
        phone = request.query_params.get("phone", "").strip()
        service_types = request.query_params.get("service_types", "").strip()
        work_years = request.query_params.get("work_years", "").strip()
        date_val = request.query_params.get("date", "").strip()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = TechnicianProfile.objects.select_related("user").exclude(verification_status="uninitiated").distinct()
        if status_val:
            qs = qs.filter(verification_status=status_val)
        if q:
            qs = qs.filter(
                Q(real_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(service_types__icontains=q)
                | Q(id_card_no__icontains=q)
                | Q(service_areas__icontains=q)
            )
        if name:
            qs = qs.filter(real_name__icontains=name)
        if phone:
            qs = qs.filter(phone__icontains=phone)
        if service_types:
            qs = qs.filter(service_types__icontains=service_types)
        if work_years:
            try:
                qs = qs.filter(work_years=int(work_years))
            except ValueError:
                pass
        if date_val:
            qs = qs.filter(updated_at__date=date_val)

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = [
            {
                "id": x.id,
                "user_id": x.user_id,
                "real_name": x.real_name,
                "phone": x.phone,
                "id_card_no": x.id_card_no,
                "gender": x.gender,
                "age": x.age,
                "service_types": x.service_types,
                "work_years": x.work_years,
                "service_areas": x.service_areas,
                "verification_status": x.verification_status,
                "is_recommended": x.is_recommended,
                "updated_at": format_dt(x.updated_at),
            }
            for x in qs.order_by("-updated_at")[start:end]
        ]
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    def delete(self, request, technician_id: int):
        profile = TechnicianProfile.objects.filter(id=technician_id).first()
        if not profile:
            raise Http404

        user = profile.user
        profile.delete()
        if user:
            user.delete()

        return Response({"ok": True})


class AdminTechnicianDetailView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, technician_id: int):
        profile = TechnicianProfile.objects.filter(id=technician_id).first()
        if not profile:
            raise Http404

        verifications = []
        latest_verification = None
        for v in profile.verifications.all().order_by("-submitted_at"):
            verifications.append({
                "id": v.id,
                "verification_type": v.verification_type,
                "status": v.status,
                "submitted_at": format_dt(v.submitted_at),
                "reviewed_at": format_dt(v.reviewed_at),
                "admin_note": v.admin_note,
            })
            if latest_verification is None:
                latest_verification = v

        def get_file_url(field):
            if field and hasattr(field, 'url'):
                return field.url
            return None

        # 生成二维码
        qr_content = f"/pages/technician-detail/technician-detail?id={profile.id}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 将二维码图片转换为 base64 编码
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        qr_data_url = f"data:image/png;base64,{qr_base64}"

        return Response({
            "id": profile.id,
            "real_name": profile.real_name,
            "phone": profile.phone,
            "id_card_no": profile.id_card_no,
            "gender": profile.gender,
            "age": profile.age,
            "bio": profile.bio,
            "service_types": profile.service_types,
            "work_years": profile.work_years,
            "service_areas": profile.service_areas,
            "health_cert": get_file_url(profile.health_cert),
            "avatar": get_file_url(profile.avatar),
            "id_card_front": get_file_url(latest_verification.id_card_front) if latest_verification else None,
            "id_card_back": get_file_url(latest_verification.id_card_back) if latest_verification else None,
            "licenses": [get_file_url(license.license_file) for license in profile.licenses.all()],
            "verification_status": profile.verification_status,
            "is_recommended": profile.is_recommended,
            "recommended_at": format_dt(profile.recommended_at),
            "verifications": verifications,
            "updated_at": format_dt(profile.updated_at),
            "qrcode": qr_data_url,
        })


class AdminTechnicianVerificationActionView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, technician_id: int, action: str):
        profile = TechnicianProfile.objects.filter(id=technician_id).first()
        if not profile:
            raise Http404

        note = (request.data.get("note") or "").strip()
        now = timezone.now()

        pending_verification = (
            profile.verifications.filter(status=TechnicianVerification.Status.PENDING)
            .order_by("-submitted_at")
            .first()
        )

        if action == "approve":
            if pending_verification:
                pending_verification.status = TechnicianVerification.Status.APPROVED
                pending_verification.admin_note = note
                pending_verification.reviewed_at = now
                pending_verification.reviewed_by = request.user
                pending_verification.save(
                    update_fields=["status", "admin_note", "reviewed_at", "reviewed_by"]
                )

            profile.verification_status = TechnicianProfile.VerificationStatus.APPROVED
            profile.is_disabled = False
            profile.save(update_fields=["verification_status", "is_disabled", "updated_at"])
            return Response({"ok": True})

        if action == "reject":
            if pending_verification:
                pending_verification.status = TechnicianVerification.Status.REJECTED
                pending_verification.admin_note = note
                pending_verification.reviewed_at = now
                pending_verification.reviewed_by = request.user
                pending_verification.save(
                    update_fields=["status", "admin_note", "reviewed_at", "reviewed_by"]
                )

            profile.verification_status = TechnicianProfile.VerificationStatus.REJECTED
            profile.is_disabled = True
            profile.save(update_fields=["verification_status", "is_disabled", "updated_at"])
            return Response({"ok": True})

        if action == "recommend":
            # 检查技师认证状态
            if profile.verification_status != TechnicianProfile.VerificationStatus.APPROVED:
                return Response({"detail": "只有认证通过的技师才能被推荐"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 切换推荐状态
            profile.is_recommended = not profile.is_recommended
            if profile.is_recommended:
                profile.recommended_at = now
            else:
                profile.recommended_at = None
            profile.save(update_fields=["is_recommended", "recommended_at", "updated_at"])
            return Response({"ok": True, "is_recommended": profile.is_recommended})

        if action == "disable":
            profile.is_disabled = True
            profile.save(update_fields=["is_disabled", "updated_at"])
            return Response({"ok": True})

        if action == "enable":
            profile.is_disabled = False
            profile.save(update_fields=["is_disabled", "updated_at"])
            return Response({"ok": True})

        return Response({"detail": "无效操作"}, status=status.HTTP_400_BAD_REQUEST)


class AdminListingsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        status_val = request.query_params.get("status")
        q = request.query_params.get("q", "").strip()
        title = request.query_params.get("title", "").strip()
        primary_category_id = request.query_params.get("primary_category_id") or request.query_params.get("category_id")
        secondary_category_id = request.query_params.get("secondary_category_id")
        publisher = request.query_params.get("publisher", "").strip()
        date_val = request.query_params.get("date", "").strip()
        show_deleted_param = request.query_params.get("show_deleted", "")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = (
            Listing.objects.select_related(
                "technician",
                "category",
            )
            .prefetch_related("services")
            .all()
        )
        if show_deleted_param == "false":
            qs = qs.filter(is_deleted=False)
        elif show_deleted_param == "true":
            qs = qs.filter(is_deleted=True)
        if status_val:
            qs = qs.filter(status=status_val)
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(contact_info__icontains=q)
                | Q(service_areas__icontains=q)
                | Q(technician__real_name__icontains=q)
            )
        if title:
            qs = qs.filter(title__icontains=title)
        if secondary_category_id:
            try:
                cid = int(secondary_category_id)
            except (TypeError, ValueError):
                return Response({"detail": "二级分类ID不合法"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(category_id__in=get_descendant_ids(cid))
        elif primary_category_id:
            try:
                cid = int(primary_category_id)
            except (TypeError, ValueError):
                return Response({"detail": "一级分类ID不合法"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(category_id__in=get_descendant_ids(cid))
        if publisher:
            qs = qs.filter(technician__real_name__icontains=publisher)
        if date_val:
            qs = qs.filter(created_at__date=date_val)

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = [
            {
                "id": x.id,
                "technician_id": x.technician_id,
                "real_name": x.technician.real_name if x.technician else None,
                "title": x.title,
                "category_id": x.category_id,
                "category_name": listing_category_payload(x)["category_path"],
                **listing_category_payload(x),
                "service_price": service_price_display(x),
                "service_areas": x.service_areas,
                "contact_info": x.contact_info,
                "is_deleted": x.is_deleted,
                "status": x.status,
                "created_at": format_dt(x.created_at),
                "updated_at": format_dt(x.updated_at),
            }
            for x in qs.order_by("-created_at")[start:end]
        ]
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })


class AdminListingDetailView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, listing_id: int):
        listing = (
            Listing.objects.filter(id=listing_id)
            .select_related(
                "technician",
                "category",
            )
            .prefetch_related("services", "audits")
            .first()
        )
        if not listing:
            raise Http404

        audits = list(listing.audits.all().order_by("-created_at"))
        audits_data = [
            {
                "id": a.id,
                "status": a.status,
                "audit_note": a.audit_note,
                "reviewed_at": format_dt(a.reviewed_at),
                "reviewed_by": a.reviewed_by.username if a.reviewed_by else None,
                "created_at": format_dt(a.created_at),
            }
            for a in audits
        ]

        return Response({
            "id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "cover_url": listing.cover_url,
            "cover_urls": _listing_cover_urls(listing),
            "listing_price": str(listing.listing_price) if listing.listing_price is not None else None,
            "listing_price_unit": listing.listing_price_unit or "次",
            "service_price": service_price_display(listing),
            "category_id": listing.category_id,
            "category_name": listing_category_payload(listing)["category_path"],
            **listing_category_payload(listing),
            "technician_id": listing.technician_id,
            "real_name": listing.technician.real_name if listing.technician else None,
            "service_areas": listing.service_areas,
            "contact_info": listing.contact_info,
            "is_deleted": listing.is_deleted,
            "status": listing.status,
            "created_at": format_dt(listing.created_at),
            "updated_at": format_dt(listing.updated_at),
            "audits": audits_data,
        })

    def delete(self, request, listing_id: int):
        listing = Listing.objects.filter(id=listing_id).first()
        if not listing:
            raise Http404
        listing.is_deleted = True
        listing.save()
        return Response({"ok": True})


class AdminListingAuditActionView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, listing_id: int, action: str):
        listing = Listing.objects.filter(id=listing_id).select_related("technician").first()
        if not listing:
            raise Http404

        note = (request.data.get("note") or "").strip()
        now = timezone.now()

        from listings.models import ListingAudit

        if action == "approve":
            listing.status = Listing.Status.PUBLISHED
            listing.audit_note = note
            listing.reviewed_at = now
            listing.audited_by = request.user
            listing.published_at = now
            listing.save(
                update_fields=[
                    "status",
                    "audit_note",
                    "reviewed_at",
                    "audited_by",
                    "published_at",
                    "updated_at",
                ]
            )
            ListingAudit.objects.create(
                listing=listing,
                status=ListingAudit.Status.PUBLISHED,
                audit_note=note,
                reviewed_at=now,
                reviewed_by=request.user
            )
            return Response({"ok": True})

        if action == "reject":
            listing.status = Listing.Status.REJECTED
            listing.audit_note = note
            listing.reviewed_at = now
            listing.audited_by = request.user
            listing.save(
                update_fields=["status", "audit_note", "reviewed_at", "audited_by", "updated_at"]
            )
            ListingAudit.objects.create(
                listing=listing,
                status=ListingAudit.Status.REJECTED,
                audit_note=note,
                reviewed_at=now,
                reviewed_by=request.user
            )
            return Response({"ok": True})

        if action == "disable":
            listing.status = Listing.Status.DISABLED
            listing.audit_note = note
            listing.reviewed_at = now
            listing.audited_by = request.user
            listing.save(
                update_fields=["status", "audit_note", "reviewed_at", "audited_by", "updated_at"]
            )
            ListingAudit.objects.create(
                listing=listing,
                status=ListingAudit.Status.DISABLED,
                audit_note=note,
                reviewed_at=now,
                reviewed_by=request.user
            )
            return Response({"ok": True})

        if action == "enable":
            listing.status = Listing.Status.PUBLISHED
            listing.audit_note = note
            listing.reviewed_at = now
            listing.audited_by = request.user
            listing.save(
                update_fields=["status", "audit_note", "reviewed_at", "audited_by", "updated_at"]
            )
            ListingAudit.objects.create(
                listing=listing,
                status=ListingAudit.Status.PUBLISHED,
                audit_note=note,
                reviewed_at=now,
                reviewed_by=request.user
            )
            return Response({"ok": True})

        return Response({"detail": "无效操作"}, status=status.HTTP_400_BAD_REQUEST)


class AdminServiceTypesView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        status_val = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = ServiceType.objects.select_related("category")
        if status_val:
            qs = qs.filter(status=status_val)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(category__name__icontains=search)
            )

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = []
        for s in qs.order_by("-updated_at")[start:end]:
            items.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "category_id": s.category_id,
                    "base_price": str(s.base_price),
                    "currency": s.currency,
                    "price_unit": s.price_unit,
                    "status": s.status,
                    "updated_at": format_dt(s.updated_at),
                }
            )
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        category_id = request.data.get("category_id")
        base_price = request.data.get("base_price")
        currency = request.data.get("currency") or ServiceType._meta.get_field("currency").default
        price_unit = request.data.get("price_unit") or "per_service"
        status_val = request.data.get("status") or ServiceType.Status.ENABLED

        if not name:
            return Response({"detail": "服务类型名称必填"}, status=status.HTTP_400_BAD_REQUEST)
        if not category_id:
            return Response({"detail": "所属分类必填"}, status=status.HTTP_400_BAD_REQUEST)
        if base_price is None or base_price == "":
            return Response({"detail": "基础价格必填"}, status=status.HTTP_400_BAD_REQUEST)

        category = Category.objects.filter(id=int(category_id)).first()
        if not category:
            return Response({"detail": "分类ID无效"}, status=status.HTTP_400_BAD_REQUEST)

        if status_val not in [ServiceType.Status.ENABLED, ServiceType.Status.DISABLED]:
            status_val = ServiceType.Status.ENABLED

        s = ServiceType.objects.create(
            name=name,
            category=category,
            base_price=base_price,
            currency=currency,
            price_unit=price_unit,
            status=status_val,
        )

        return Response({"ok": True, "id": s.id}, status=status.HTTP_201_CREATED)


class AdminServiceTypeDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, service_type_id: int):
        s = ServiceType.objects.filter(id=service_type_id).first()
        if not s:
            raise Http404

        name = request.data.get("name")
        if name is not None:
            name = str(name).strip()
            if not name:
                return Response({"detail": "服务类型名称不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            s.name = name

        if "base_price" in request.data:
            s.base_price = request.data.get("base_price")

        if "status" in request.data:
            status_val = request.data.get("status")
            if status_val in [ServiceType.Status.ENABLED, ServiceType.Status.DISABLED]:
                s.status = status_val

        if "category_id" in request.data:
            category_id = request.data.get("category_id")
            if category_id:
                category = Category.objects.filter(id=int(category_id)).first()
                if not category:
                    return Response({"detail": "分类ID无效"}, status=status.HTTP_400_BAD_REQUEST)
                s.category = category

        s.save()
        return Response({"ok": True})




class AdminRegisteredUsersView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        search = request.query_params.get("search", "").strip()
        phone_search = request.query_params.get("phone", "").strip()
        date_val = request.query_params.get("date", "")
        status_filter = request.query_params.get("status", "")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = User.objects.filter(is_staff=False).select_related("technician_profile")

        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(technician_profile__phone__icontains=q)
            ).distinct()
        elif search:
            qs = qs.filter(
                Q(username__icontains=search) | Q(first_name__icontains=search)
            ).distinct()

        if phone_search:
            qs = qs.filter(technician_profile__phone__icontains=phone_search)

        if date_val:
            qs = qs.filter(date_joined__date=date_val)

        if status_filter == "active":
            qs = qs.filter(is_active=True)
        elif status_filter == "disabled":
            qs = qs.filter(is_active=False)

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = []
        for u in qs.order_by("-date_joined")[start:end]:
            tp = getattr(u, "technician_profile", None)
            items.append({
                "id": u.id,
                "username": u.username,
                "phone": tp.phone if tp else None,
                "is_active": u.is_active,
                "date_joined": str(u.date_joined),
                "last_login": str(u.last_login) if u.last_login else None,
            })
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        password = request.data.get("password", "")
        is_active = request.data.get("is_active", True)

        if not phone:
            return Response({"detail": "手机号必填"}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"detail": "密码必填"}, status=status.HTTP_400_BAD_REQUEST)

        # 验证手机号格式
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, phone):
            return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)

        # 自动生成用户名（如果未提供）
        if not username:
            import random
            prefix = "用户_"
            phone_last4 = phone[-4:]
            random_digit = random.randint(0, 9)
            username = f"{prefix}{phone_last4}{random_digit}"

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return Response({"detail": "用户名已存在"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查手机号是否已被其他用户使用
        from listings.models import TechnicianProfile
        if TechnicianProfile.objects.filter(phone=phone).exists():
            return Response({"detail": "该手机号已被使用"}, status=status.HTTP_400_BAD_REQUEST)

        # 创建用户
        user = User.objects.create_user(
            username=username,
            password=password,
            is_active=is_active,
            is_staff=False,
        )

        # 创建技师资料（如果提供了手机号）
        if phone:
            TechnicianProfile.objects.create(
                user=user,
                phone=phone,
                verification_status="uninitiated",
            )

        return Response({"ok": True, "id": user.id}, status=status.HTTP_201_CREATED)


class AdminRegisteredUserDetailView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, user_id: int):
        user = User.objects.filter(id=user_id, is_staff=False).select_related("technician_profile").first()
        if not user:
            raise Http404
        tp = getattr(user, "technician_profile", None)
        return Response({
            "id": user.id,
            "username": user.username,
            "phone": tp.phone if tp else None,
            "is_active": user.is_active,
            "date_joined": str(user.date_joined),
            "last_login": str(user.last_login) if user.last_login else None,
        })

    def patch(self, request, user_id: int):
        user = User.objects.filter(id=user_id, is_staff=False).first()
        if not user:
            raise Http404
        is_active = request.data.get("is_active")
        if is_active is not None:
            user.is_active = is_active
            user.save(update_fields=["is_active"])
        return Response({"ok": True})


class AdminRegisteredUserResetPasswordView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, user_id: int):
        user = User.objects.filter(id=user_id, is_staff=False).first()
        if not user:
            raise Http404
        tp = getattr(user, "technician_profile", None)
        if tp and tp.phone:
            new_password = tp.phone[-6:]
        else:
            new_password = user.username[-6:] if user.username else "123456"
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"ok": True, "new_password": new_password})


class AdminAdminUsersView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        status_filter = request.query_params.get("status", "")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = User.objects.filter(is_staff=True)
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(email__icontains=search)
            ).distinct()
        if status_filter == "active":
            qs = qs.filter(is_active=True)
        elif status_filter == "inactive":
            qs = qs.filter(is_active=False)

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = []
        for u in qs.order_by("-date_joined")[start:end]:
            items.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "first_name": u.first_name,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "date_joined": str(u.date_joined),
                "last_login": str(u.last_login) if u.last_login else None,
            })
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password", "")
        email = (request.data.get("email") or "").strip()
        first_name = (request.data.get("first_name") or "").strip()
        is_superuser = request.data.get("is_superuser", False)

        if not username:
            return Response({"detail": "用户名必填"}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"detail": "密码必填"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"detail": "用户名已存在"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"detail": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            is_staff=True,
            is_superuser=is_superuser,
        )
        return Response({"ok": True, "id": user.id}, status=status.HTTP_201_CREATED)


class AdminAdminUserDetailView(APIView):
    permission_classes = [IsOperator]

    def patch(self, request, user_id: int):
        user = User.objects.filter(id=user_id, is_staff=True).first()
        if not user:
            raise Http404

        first_name = request.data.get("first_name")
        if first_name is not None:
            user.first_name = str(first_name).strip()

        email = request.data.get("email")
        if email is not None:
            user.email = str(email).strip()

        is_active = request.data.get("is_active")
        if is_active is not None:
            user.is_active = bool(is_active)

        is_superuser = request.data.get("is_superuser")
        if is_superuser is not None:
            user.is_superuser = bool(is_superuser)

        user.save()
        return Response({"ok": True})

    def delete(self, request, user_id: int):
        user = User.objects.filter(id=user_id, is_staff=True).first()
        if not user:
            raise Http404

        if user.id == request.user.id:
            return Response({"detail": "不能删除自己"}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({"ok": True})


class AdminCurrentUserView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "avatar_url": user.first_name[:1].upper() if user.first_name else user.username[:1].upper(),
        })


class AdminChangePasswordView(APIView):
    permission_classes = [IsOperator]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")

        if not old_password or not new_password:
            return Response({"detail": "旧密码和新密码必填"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"detail": "旧密码错误"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({"detail": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"ok": True})


class AdminProfileView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
        })

    def patch(self, request):
        user = request.user

        first_name = request.data.get("first_name")
        if first_name is not None:
            user.first_name = str(first_name).strip()

        email = request.data.get("email")
        if email is not None:
            user.email = str(email).strip()

        user.save()
        return Response({"ok": True})


class AdminBannersView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        status_val = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = Banner.objects.all()
        if status_val:
            qs = qs.filter(status=status_val)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(link_value__icontains=search))

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = [
            {
                "id": x.id,
                "title": x.title,
                "image_url": x.image.url if x.image else x.image_url,
                "link_type": x.link_type,
                "link_value": x.link_value,
                "sort_order": x.sort_order,
                "status": x.status,
                "created_at": format_dt(x.created_at),
            }
            for x in qs.order_by("sort_order", "-created_at")[start:end]
        ]
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    def post(self, request):
        title = (request.data.get("title") or "").strip()
        image_file = request.FILES.get("image")
        image_url = (request.data.get("image_url") or "").strip()
        link_type = request.data.get("link_type") or Banner.LinkType.NONE
        link_value = (request.data.get("link_value") or "").strip()
        sort_order = int(request.data.get("sort_order") or 0)
        status_val = request.data.get("status") or Banner.Status.ENABLED

        if not image_file and not image_url:
            return Response({"detail": "请上传图片或填写图片URL"}, status=status.HTTP_400_BAD_REQUEST)

        if link_type not in [Banner.LinkType.NONE, Banner.LinkType.CATEGORY, Banner.LinkType.LISTING, Banner.LinkType.URL]:
            return Response({"detail": "跳转类型无效"}, status=status.HTTP_400_BAD_REQUEST)

        if status_val not in [Banner.Status.ENABLED, Banner.Status.DISABLED]:
            status_val = Banner.Status.ENABLED

        banner = Banner.objects.create(
            title=title,
            image=image_file if image_file else None,
            image_url=image_url,
            link_type=link_type,
            link_value=link_value,
            sort_order=sort_order,
            status=status_val,
        )
        return Response({"ok": True, "id": banner.id}, status=status.HTTP_201_CREATED)


class AdminBannerDetailView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, banner_id: int):
        banner = Banner.objects.filter(id=banner_id).first()
        if not banner:
            raise Http404

        title = request.data.get("title")
        if title is not None:
            banner.title = str(title).strip()

        image_file = request.FILES.get("image")
        if image_file:
            banner.image = image_file

        image_url = request.data.get("image_url")
        if image_url is not None:
            banner.image_url = str(image_url).strip()

        link_type = request.data.get("link_type")
        if link_type is not None:
            if link_type not in [Banner.LinkType.NONE, Banner.LinkType.CATEGORY, Banner.LinkType.LISTING, Banner.LinkType.URL]:
                return Response({"detail": "跳转类型无效"}, status=status.HTTP_400_BAD_REQUEST)
            banner.link_type = link_type

        link_value = request.data.get("link_value")
        if link_value is not None:
            banner.link_value = str(link_value).strip()

        sort_order = request.data.get("sort_order")
        if sort_order is not None:
            banner.sort_order = int(sort_order)

        status_val = request.data.get("status")
        if status_val in [Banner.Status.ENABLED, Banner.Status.DISABLED]:
            banner.status = status_val

        banner.save()
        return Response({"ok": True})

    def delete(self, request, banner_id: int):
        banner = Banner.objects.filter(id=banner_id).first()
        if not banner:
            raise Http404
        banner.delete()
        return Response({"ok": True})


class AdminHotServicesView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        status_val = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        qs = HotService.objects.all()
        if status_val:
            qs = qs.filter(status=status_val)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(link_value__icontains=search))

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = [
            {
                "id": x.id,
                "name": x.name,
                "icon": x.icon.url if x.icon else None,
                "link_type": x.link_type,
                "link_value": x.link_value,
                "sort_order": x.sort_order,
                "status": x.status,
                "created_at": format_dt(x.created_at),
            }
            for x in qs.order_by("-sort_order", "-created_at")[start:end]
        ]
        return Response({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        icon_file = request.FILES.get("icon")
        link_type = request.data.get("link_type") or HotService.LinkType.NONE
        link_value = (request.data.get("link_value") or "").strip()
        sort_order = int(request.data.get("sort_order") or 0)
        status_val = request.data.get("status") or HotService.Status.ENABLED

        if not name:
            return Response({"detail": "名称必填"}, status=status.HTTP_400_BAD_REQUEST)

        if status_val not in [HotService.Status.ENABLED, HotService.Status.DISABLED]:
            status_val = HotService.Status.ENABLED

        hs = HotService.objects.create(
            name=name,
            icon=icon_file,
            link_type=link_type,
            link_value=link_value,
            sort_order=sort_order,
            status=status_val,
        )
        return Response({"ok": True, "id": hs.id}, status=status.HTTP_201_CREATED)


class AdminHotServiceDetailView(APIView):
    permission_classes = [IsOperator]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, hot_service_id: int):
        hs = HotService.objects.filter(id=hot_service_id).first()
        if not hs:
            raise Http404
        return Response({
            "id": hs.id,
            "name": hs.name,
            "icon": hs.icon.url if hs.icon else None,
            "link_type": hs.link_type,
            "link_value": hs.link_value,
            "sort_order": hs.sort_order,
            "status": hs.status,
            "created_at": format_dt(hs.created_at),
            "updated_at": format_dt(hs.updated_at),
        })

    def patch(self, request, hot_service_id: int):
        hs = HotService.objects.filter(id=hot_service_id).first()
        if not hs:
            raise Http404

        icon_file = request.FILES.get("icon")
        if icon_file:
            hs.icon = icon_file
        if "name" in request.data:
            hs.name = request.data["name"].strip()
        if "link_type" in request.data:
            hs.link_type = request.data["link_type"]
        if "link_value" in request.data:
            hs.link_value = request.data["link_value"].strip()
        if "sort_order" in request.data:
            hs.sort_order = int(request.data["sort_order"])
        if "status" in request.data:
            status_val = request.data["status"]
            if status_val in [HotService.Status.ENABLED, HotService.Status.DISABLED]:
                hs.status = status_val

        hs.save()
        return Response({"ok": True})

    def delete(self, request, hot_service_id: int):
        hs = HotService.objects.filter(id=hot_service_id).first()
        if not hs:
            raise Http404
        hs.delete()
        return Response({"ok": True})
