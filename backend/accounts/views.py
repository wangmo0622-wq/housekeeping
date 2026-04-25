import base64
import logging
import json
import os
import random
import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from uuid import uuid4

import qrcode
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

import requests
from accounts.models import (
    Organization,
    OrganizationTechnician,
    TechnicianLicense,
    TechnicianProfile,
    TechnicianVerification,
)
from catalog.models import Category
from listings.models import Listing
from listings.serializers import listing_category_payload, service_price_display

# 配置日志
logger = logging.getLogger(__name__)


REGION_DICT_FILE = os.path.join(settings.BASE_DIR, "data", "regions_cn_pca.json")
_REGION_DICT_CACHE = None


def get_region_dict():
    global _REGION_DICT_CACHE
    if _REGION_DICT_CACHE is not None:
        return _REGION_DICT_CACHE

    fallback = {
        "provinces": [{"code": "360000", "name": "江西省"}],
        "cities": {"360000": [{"code": "360700", "name": "赣州市"}]},
        "districts": {"360700": [{"code": "360702", "name": "章贡区"}]},
        "default": {"province_code": "360000", "city_code": "360700", "district_code": "360702"},
    }

    try:
        with open(REGION_DICT_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict) and loaded.get("provinces"):
            _REGION_DICT_CACHE = loaded
            return _REGION_DICT_CACHE
    except Exception as exc:
        logger.warning("load region dict failed: %s", exc)

    _REGION_DICT_CACHE = fallback
    return _REGION_DICT_CACHE



def generate_username(phone):
    """
    生成用户名：前缀 + 手机尾4位 + 1位随机数字
    例如：用户_68923
    """
    prefix = "用户_"
    phone_last4 = phone[-4:]
    random_digit = random.randint(0, 9)
    return f"{prefix}{phone_last4}{random_digit}"


def is_valid_mainland_phone(phone: str) -> bool:
    return bool(re.match(r"^1[3-9]\d{9}$", phone or ""))


def get_user_organization_or_404(user):
    try:
        return user.organization, None
    except Organization.DoesNotExist:
        return None, Response({"detail": "机构资料不存在"}, status=status.HTTP_404_NOT_FOUND)


def get_org_active_technician_ids(organization: Organization):
    return list(
        OrganizationTechnician.objects.filter(
            organization=organization,
            status=OrganizationTechnician.Status.ACTIVE,
        ).values_list("technician_id", flat=True)
    )


def _format_dt(dt):
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _listing_cover_urls_list(listing: Listing) -> list:
    if listing.cover_urls:
        return list(listing.cover_urls)[: Listing.MAX_COVER_URLS]
    return [listing.cover_url] if listing.cover_url else []


def _org_save_upload_and_url(upload, prefix: str) -> str:
    ext = os.path.splitext(upload.name or "")[-1] or ".jpg"
    path = default_storage.save(f"{prefix}/{uuid4()}{ext}", upload)
    return default_storage.url(path)


def _technician_file_url(field):
    if field and hasattr(field, "url"):
        return field.url
    return None


def organization_technician_detail_payload(profile: TechnicianProfile) -> dict:
    """与管理端技师详情口径一致，供机构后台抽屉编辑使用。"""
    verifications = []
    latest_verification = None
    for v in profile.verifications.all().order_by("-submitted_at"):
        verifications.append(
            {
                "id": v.id,
                "verification_type": v.verification_type,
                "status": v.status,
                "submitted_at": _format_dt(v.submitted_at),
                "reviewed_at": _format_dt(v.reviewed_at),
                "admin_note": v.admin_note,
            }
        )
        if latest_verification is None:
            latest_verification = v

    qr_content = f"/pages/technician-detail/technician-detail?id={profile.id}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_data_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

    return {
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
        "health_cert": _technician_file_url(profile.health_cert),
        "avatar": _technician_file_url(profile.avatar),
        "id_card_front": _technician_file_url(latest_verification.id_card_front) if latest_verification else None,
        "id_card_back": _technician_file_url(latest_verification.id_card_back) if latest_verification else None,
        "licenses": [_technician_file_url(lic.license_file) for lic in profile.licenses.all()],
        "verification_status": profile.verification_status,
        "is_disabled": profile.is_disabled,
        "is_recommended": profile.is_recommended,
        "recommended_at": _format_dt(profile.recommended_at),
        "verifications": verifications,
        "updated_at": _format_dt(profile.updated_at),
        "qrcode": qr_data_url,
    }


def organization_listing_detail_payload(listing: Listing) -> dict:
    audits = list(listing.audits.all().order_by("-created_at"))
    audits_data = [
        {
            "id": a.id,
            "status": a.status,
            "audit_note": a.audit_note,
            "reviewed_at": _format_dt(a.reviewed_at),
            "reviewed_by": a.reviewed_by.username if a.reviewed_by else None,
            "created_at": _format_dt(a.created_at),
        }
        for a in audits
    ]
    cat_payload = listing_category_payload(listing)
    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "cover_url": listing.cover_url,
        "cover_urls": _listing_cover_urls_list(listing),
        "listing_price": str(listing.listing_price) if listing.listing_price is not None else None,
        "listing_price_unit": listing.listing_price_unit or "次",
        "service_price": service_price_display(listing),
        "category_id": listing.category_id,
        "category_name": cat_payload["category_path"],
        **cat_payload,
        "technician_id": listing.technician_id,
        "real_name": listing.technician.real_name if listing.technician else None,
        "service_areas": listing.service_areas,
        "contact_info": listing.contact_info,
        "is_deleted": listing.is_deleted,
        "status": listing.status,
        "created_at": _format_dt(listing.created_at),
        "updated_at": _format_dt(listing.updated_at),
        "audits": audits_data,
    }


class MiniProgramUserSerializer:
    @staticmethod
    def get_user_info(user):
        from accounts.models import TechnicianProfile, Organization
        phone = None
        
        # 检查是否为技师
        try:
            tech_profile = user.technician_profile
            is_technician = True
            technician_status = tech_profile.verification_status
            technician_id = tech_profile.id
            phone = tech_profile.phone
        except TechnicianProfile.DoesNotExist:
            is_technician = False
            technician_status = None
            technician_id = None
        
        # 检查是否为机构
        try:
            organization = user.organization
            is_organization = True
            organization_id = organization.id
            organization_name = organization.company_name
            organization_status = organization.verification_status
            if not phone:
                phone = organization.contact_phone
        except Organization.DoesNotExist:
            is_organization = False
            organization_id = None
            organization_name = None
            organization_status = None

        return {
            "id": user.id,
            "username": user.username,
            "phone": phone,
            "is_technician": is_technician,
            "technician_status": technician_status,
            "technician_id": technician_id,
            "is_organization": is_organization,
            "organization_id": organization_id,
            "organization_name": organization_name,
            "organization_status": organization_status,
        }


def wechat_jscode_to_session(code: str) -> dict:
    """
    用 wx.login 返回的 code 换取 openid。
    参考：https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/login/auth.code2Session.html
    """

    appid = getattr(settings, "WECHAT_APPID", None)
    secret = getattr(settings, "WECHAT_SECRET", None)
    if not appid or not secret:
        logger.error("WECHAT_APPID 或 WECHAT_SECRET 未配置")
        raise RuntimeError("WECHAT_APPID / WECHAT_SECRET 未配置")

    url = "https://api.weixin.qq.com/sns/jscode2session"
    try:
        resp = requests.get(
            url,
            params={
                "appid": appid,
                "secret": secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        data = resp.json()
        if resp.status_code != 200 or "openid" not in data:
            logger.error(f"微信登录失败: {data}")
            raise RuntimeError(f"微信登录失败: {data}")
        return data
    except requests.RequestException as e:
        logger.error(f"微信 API 请求失败: {str(e)}")
        raise RuntimeError(f"微信 API 请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"微信登录处理失败: {str(e)}")
        raise RuntimeError(f"微信登录处理失败: {str(e)}")


class WechatLoginView(APIView):
    """
    小程序端登录：返回 SimpleJWT token。
    说明：管理端登录不走这个接口。
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "微信 code 必填"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = wechat_jscode_to_session(code)
        except Exception as e:
            logger.error(f"微信登录失败: {str(e)}")
            return Response({"detail": "微信登录失败"}, status=status.HTTP_400_BAD_REQUEST)

        openid = data["openid"]

        try:
            user, _created = User.objects.get_or_create(
                username=openid,
                defaults={
                    "is_active": True,
                    "first_name": f"用户{openid[-6:]}",
                },
            )

            refresh = RefreshToken.for_user(user)
            user_info = MiniProgramUserSerializer.get_user_info(user)
            
            # 如果有手机号，确保存储到技师资料
            nickname = request.data.get("nickname")
            # 注意：微信登录接口目前不接收手机号参数，需要在用户后续绑定手机号时处理

            logger.info(f"用户微信登录成功: {user.username}")
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": user_info,
                }
            )
        except Exception as e:
            logger.error(f"用户登录处理失败: {str(e)}")
            return Response({"detail": "登录处理失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    """
    退出登录：客户端丢弃 token 即可。未启用 token_blacklist 时服务端无法吊销 refresh。
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                blacklist = getattr(token, "blacklist", None)
                if callable(blacklist):
                    blacklist()
            return Response({"ok": True})
        except Exception:
            return Response({"ok": True})


class PhoneRegisterView(APIView):
    """
    手机号注册
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        password = request.data.get("password") or ""

        if not phone:
            return Response({"detail": "手机号不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({"detail": "密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({"detail": "密码长度不能少于6位"}, status=status.HTTP_400_BAD_REQUEST)

        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, phone):
            return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查手机号是否已被注册
        from accounts.models import TechnicianProfile
        if TechnicianProfile.objects.filter(phone=phone).exists():
            return Response({"detail": "该手机号已注册"}, status=status.HTTP_400_BAD_REQUEST)

        # 自动生成用户名
        username = generate_username(phone)

        user = User.objects.create(
            username=username,
            password=make_password(password),
            is_active=True,
            first_name=f"用户{phone[-4:]}",
        )

        # 创建技师资料并存储手机号
        from accounts.models import TechnicianProfile
        TechnicianProfile.objects.create(
            user=user,
            phone=phone,
            verification_status="uninitiated",
        )

        refresh = RefreshToken.for_user(user)
        user_info = MiniProgramUserSerializer.get_user_info(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_info,
            },
            status=status.HTTP_201_CREATED,
        )


class PhoneLoginView(APIView):
    """
    手机号登录
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        password = request.data.get("password") or ""

        if not phone:
            return Response({"detail": "手机号不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({"detail": "密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        # 通过技师资料中的手机号查找用户
        from accounts.models import TechnicianProfile
        try:
            tech_profile = TechnicianProfile.objects.get(phone=phone)
            user = tech_profile.user
        except TechnicianProfile.DoesNotExist:
            return Response({"detail": "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({"detail": "密码错误"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"detail": "账号已被禁用"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        user_info = MiniProgramUserSerializer.get_user_info(user)
        # 确保返回手机号
        user_info["phone"] = phone

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_info,
            }
        )


class UserProfileView(APIView):
    """
    用户资料管理
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """获取用户资料"""
        user = request.user
        user_info = MiniProgramUserSerializer.get_user_info(user)
        # 获取手机号
        from accounts.models import TechnicianProfile
        try:
            tech_profile = user.technician_profile
            user_info["phone"] = tech_profile.phone
        except TechnicianProfile.DoesNotExist:
            pass
        return Response(user_info)
    
    def patch(self, request):
        """更新用户资料"""
        user = request.user
        phone = (request.data.get("phone") or "").strip()
        
        if phone:
            # 验证手机号格式
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, phone):
                return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 检查手机号是否已被其他用户使用
            from accounts.models import TechnicianProfile
            existing_profile = TechnicianProfile.objects.filter(phone=phone).exclude(user=user).first()
            if existing_profile:
                return Response({"detail": "该手机号已被使用"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新手机号
            try:
                tech_profile = user.technician_profile
                tech_profile.phone = phone
                tech_profile.save(update_fields=["phone"])
            except TechnicianProfile.DoesNotExist:
                # 如果没有技师资料，创建一个
                TechnicianProfile.objects.create(
                    user=user,
                    phone=phone,
                    verification_status="uninitiated",
                )
        
        user_info = MiniProgramUserSerializer.get_user_info(user)
        user_info["phone"] = phone or getattr(user.technician_profile, "phone", None)
        
        return Response(user_info)


class OrganizationRegisterView(APIView):
    """
    机构（企业）注册
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 兼容旧参数：phone；默认用该手机号作为机构登录手机号
        phone = (request.data.get("phone") or request.data.get("contact_phone") or "").strip()
        password = request.data.get("password") or ""
        company_name = (request.data.get("company_name") or "").strip()
        contact_person = (request.data.get("contact_person") or "").strip()
        contact_phone = (request.data.get("contact_phone") or phone).strip()

        if not phone:
            return Response({"detail": "手机号不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({"detail": "密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({"detail": "密码长度不能少于6位"}, status=status.HTTP_400_BAD_REQUEST)

        if not is_valid_mainland_phone(phone):
            return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
        if not is_valid_mainland_phone(contact_phone):
            return Response({"detail": "联系电话格式不正确"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查手机号是否已被注册
        if (
            TechnicianProfile.objects.filter(phone=phone).exists()
            or TechnicianProfile.objects.filter(phone=contact_phone).exists()
            or Organization.objects.filter(contact_phone=phone).exists()
            or Organization.objects.filter(contact_phone=contact_phone).exists()
        ):
            return Response({"detail": "该手机号已注册"}, status=status.HTTP_400_BAD_REQUEST)

        # 自动生成用户名
        username = generate_username(phone)

        user = User.objects.create(
            username=username,
            password=make_password(password),
            is_active=True,
            first_name=f"机构{phone[-4:]}「{company_name[:4]}」",
        )

        # 创建机构资料
        organization = Organization.objects.create(
            user=user,
            company_name=company_name,
            contact_person=contact_person,
            contact_phone=contact_phone,
            verification_status="uninitiated",
        )

        refresh = RefreshToken.for_user(user)
        user_info = MiniProgramUserSerializer.get_user_info(user)
        # 添加机构信息
        user_info["is_organization"] = True
        user_info["organization_id"] = organization.id
        user_info["organization_name"] = organization.company_name
        user_info["phone"] = contact_phone

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_info,
            },
            status=status.HTTP_201_CREATED,
        )


class OrganizationLoginView(APIView):
    """
    机构（企业）登录
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        password = request.data.get("password") or ""

        if not phone:
            return Response({"detail": "手机号不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({"detail": "密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        # 通过机构资料中的联系电话查找用户
        organization = Organization.objects.filter(contact_phone=phone).first()
        if not organization:
            return Response({"detail": "机构不存在"}, status=status.HTTP_400_BAD_REQUEST)
        user = organization.user

        if not check_password(password, user.password):
            return Response({"detail": "密码错误"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"detail": "账号已被禁用"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        user_info = MiniProgramUserSerializer.get_user_info(user)
        # 添加机构信息
        user_info["is_organization"] = True
        user_info["organization_id"] = organization.id
        user_info["organization_name"] = organization.company_name
        user_info["phone"] = phone

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_info,
            }
        )




class RegionDictView(APIView):
    """地区字典接口（省/市/县三级）"""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        level = str(request.query_params.get("level") or "province").strip().lower()
        parent_code = str(request.query_params.get("parent_code") or "").strip()

        region_dict = get_region_dict()

        if level == "province":
            items = [
                {"code": x["code"], "name": x["name"], "parent_code": "", "level": "province"}
                for x in region_dict.get("provinces", [])
            ]
        elif level == "city":
            if not parent_code:
                return Response({"detail": "parent_code 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            items = [
                {"code": x["code"], "name": x["name"], "parent_code": parent_code, "level": "city"}
                for x in region_dict.get("cities", {}).get(parent_code, [])
            ]
        elif level == "district":
            if not parent_code:
                return Response({"detail": "parent_code 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            items = [
                {"code": x["code"], "name": x["name"], "parent_code": parent_code, "level": "district"}
                for x in region_dict.get("districts", {}).get(parent_code, [])
            ]
        else:
            return Response({"detail": "level 参数不合法"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"items": items, "default": region_dict.get("default", {})})




class OrganizationChangePasswordView(APIView):
    """机构修改密码（需校验原密码）"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        old_password = str(request.data.get("old_password") or "")
        new_password = str(request.data.get("new_password") or "")

        if not old_password:
            return Response({"detail": "请输入原密码"}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({"detail": "请输入新密码"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({"detail": "新密码长度不能少于6位"}, status=status.HTTP_400_BAD_REQUEST)
        if old_password == new_password:
            return Response({"detail": "新密码不能与原密码一致"}, status=status.HTTP_400_BAD_REQUEST)

        user = organization.user
        if not check_password(old_password, user.password):
            return Response({"detail": "原密码不正确"}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save(update_fields=["password"])
        return Response({"ok": True})


class OrganizationProfileView(APIView):
    """
    机构资料管理
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request):
        """获取机构资料"""
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error
        return Response(
            {
                "id": organization.id,
                "company_name": organization.company_name,
                "contact_person": organization.contact_person,
                "contact_phone": organization.contact_phone,
                "address": organization.address,
                "business_license_number": organization.business_license_number,
                "business_license": organization.business_license.url if organization.business_license else None,
                "verification_status": organization.verification_status,
                "is_disabled": organization.is_disabled,
            }
        )

    def patch(self, request):
        """更新机构资料"""
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        if organization.verification_status == Organization.VerificationStatus.APPROVED:
            return Response({"detail": "机构认证已完成，暂不支持修改资料"}, status=status.HTTP_400_BAD_REQUEST)

        if "company_name" in request.data:
            organization.company_name = str(request.data["company_name"] or "").strip()
        if "contact_person" in request.data:
            organization.contact_person = str(request.data["contact_person"] or "").strip()
        if "contact_phone" in request.data:
            contact_phone = str(request.data["contact_phone"] or "").strip()
            if not is_valid_mainland_phone(contact_phone):
                return Response({"detail": "联系电话格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
            if (
                Organization.objects.filter(contact_phone=contact_phone)
                .exclude(id=organization.id)
                .exists()
            ):
                return Response({"detail": "联系电话已被使用"}, status=status.HTTP_400_BAD_REQUEST)
            organization.contact_phone = contact_phone
        if "address" in request.data:
            organization.address = str(request.data["address"] or "").strip()
        if "business_license_number" in request.data:
            organization.business_license_number = str(request.data["business_license_number"] or "").strip()
        remove_business_license = str(request.data.get("remove_business_license") or "").strip().lower() in {"1", "true", "yes", "on"}
        business_license_file = request.FILES.get("business_license")
        if business_license_file:
            organization.business_license = business_license_file
        elif remove_business_license and organization.business_license:
            organization.business_license.delete(save=False)
            organization.business_license = None

        organization.save()

        return Response(
            {
                "id": organization.id,
                "company_name": organization.company_name,
                "contact_person": organization.contact_person,
                "contact_phone": organization.contact_phone,
                "address": organization.address,
                "business_license_number": organization.business_license_number,
                "business_license": organization.business_license.url if organization.business_license else None,
                "verification_status": organization.verification_status,
                "is_disabled": organization.is_disabled,
            }
        )


class OrganizationVerificationSubmitView(APIView):
    """
    机构补充资料后提交认证
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error
        if organization.is_disabled:
            return Response({"detail": "机构已被禁用"}, status=status.HTTP_403_FORBIDDEN)
        if organization.verification_status == Organization.VerificationStatus.APPROVED:
            return Response({"detail": "机构已认证通过，无需重复提交"}, status=status.HTTP_400_BAD_REQUEST)

        if not organization.company_name:
            return Response({"detail": "请先补充企业名称"}, status=status.HTTP_400_BAD_REQUEST)
        if not organization.contact_person:
            return Response({"detail": "请先补充联系人"}, status=status.HTTP_400_BAD_REQUEST)
        if not organization.contact_phone or not is_valid_mainland_phone(organization.contact_phone):
            return Response({"detail": "请先补充正确的联系电话"}, status=status.HTTP_400_BAD_REQUEST)
        if not organization.business_license:
            return Response({"detail": "请先上传营业执照"}, status=status.HTTP_400_BAD_REQUEST)

        organization.verification_status = Organization.VerificationStatus.PENDING
        organization.save(update_fields=["verification_status", "updated_at"])
        return Response({"ok": True, "verification_status": organization.verification_status})


class OrganizationTechnicianView(APIView):
    """
    机构管理技师
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        """绑定已认证通过技师到机构"""
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error
        if organization.verification_status != Organization.VerificationStatus.APPROVED:
            return Response({"detail": "机构认证通过后才能绑定技师"}, status=status.HTTP_400_BAD_REQUEST)

        raw_phone = str(request.data.get("phone") or "").strip()
        phone_digits = re.sub(r"\D", "", raw_phone) if raw_phone else ""
        technician_id = request.data.get("technician_id")

        technician = None
        if phone_digits:
            if not is_valid_mainland_phone(phone_digits):
                return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
            technician = TechnicianProfile.objects.filter(phone=phone_digits).first()
            if not technician:
                return Response({"detail": "未找到该手机号对应的技师"}, status=status.HTTP_404_NOT_FOUND)
        elif technician_id is not None and technician_id != "":
            try:
                tid = int(technician_id)
            except (TypeError, ValueError):
                return Response({"detail": "技师ID无效"}, status=status.HTTP_400_BAD_REQUEST)
            technician = TechnicianProfile.objects.filter(id=tid).first()
            if not technician:
                return Response({"detail": "技师不存在"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"detail": "请填写已认证技师的手机号"}, status=status.HTTP_400_BAD_REQUEST)

        # 需求约束：认证通过后才能绑定到机构
        if technician.verification_status != TechnicianProfile.VerificationStatus.APPROVED:
            return Response({"detail": "技师认证通过后才能绑定机构"}, status=status.HTTP_400_BAD_REQUEST)

        relation, created = OrganizationTechnician.objects.get_or_create(
            organization=organization,
            technician=technician,
            defaults={"status": OrganizationTechnician.Status.ACTIVE},
        )
        if not created:
            relation.status = OrganizationTechnician.Status.ACTIVE
            relation.save(update_fields=["status", "updated_at"])

        return Response({"ok": True, "status": relation.status})
    
    def get(self, request):
        """获取机构管理的技师列表；?relation_id= 返回单条详情（与管理端字段一致）"""
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        relation_id = (request.query_params.get("relation_id") or "").strip()
        if relation_id:
            relation = (
                OrganizationTechnician.objects.filter(id=relation_id, organization=organization)
                .select_related("technician")
                .prefetch_related(
                    "technician__verifications",
                    "technician__licenses",
                )
                .first()
            )
            if not relation:
                return Response({"detail": "绑定关系不存在"}, status=status.HTTP_404_NOT_FOUND)
            data = organization_technician_detail_payload(relation.technician)
            data["relation_id"] = relation.id
            data["bind_status"] = relation.status
            return Response(data)

        technician_relations = OrganizationTechnician.objects.filter(
            organization=organization
        ).select_related("technician", "technician__user")

        technicians = []
        for relation in technician_relations:
            tech = relation.technician
            technicians.append(
                {
                    "relation_id": relation.id,
                    "id": tech.id,
                    "real_name": tech.real_name,
                    "phone": tech.phone,
                    "status": relation.status,
                    "verification_status": tech.verification_status,
                    "created_at": relation.created_at,
                }
            )

        return Response(technicians)

    def patch(self, request):
        """更新机构名下技师资料（按 relation_id）"""
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        relation_id = request.data.get("relation_id")
        if not relation_id:
            return Response({"detail": "relation_id 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        relation = OrganizationTechnician.objects.filter(id=relation_id, organization=organization).select_related("technician").first()
        if not relation:
            return Response({"detail": "绑定关系不存在"}, status=status.HTTP_404_NOT_FOUND)

        technician = relation.technician
        changed = []

        def to_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        for field in ("real_name", "id_card_no", "bio", "service_types", "service_areas"):
            if field in request.data:
                setattr(technician, field, str(request.data.get(field) or "").strip())
                changed.append(field)

        if "phone" in request.data:
            phone = str(request.data.get("phone") or "").strip()
            if phone and not is_valid_mainland_phone(phone):
                return Response({"detail": "手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
            if TechnicianProfile.objects.filter(phone=phone).exclude(id=technician.id).exists():
                return Response({"detail": "手机号已被使用"}, status=status.HTTP_400_BAD_REQUEST)
            technician.phone = phone
            changed.append("phone")

        if "gender" in request.data:
            gender = str(request.data.get("gender") or "").strip()
            if gender and gender not in {c[0] for c in TechnicianProfile.Gender.choices}:
                return Response({"detail": "性别参数不合法"}, status=status.HTTP_400_BAD_REQUEST)
            technician.gender = gender
            changed.append("gender")

        if "work_years" in request.data:
            try:
                work_years = int(request.data.get("work_years") or 0)
            except (TypeError, ValueError):
                return Response({"detail": "工作年限必须为整数"}, status=status.HTTP_400_BAD_REQUEST)
            if work_years < 0 or work_years > 4:
                return Response({"detail": "工作年限需在 0-4 之间"}, status=status.HTTP_400_BAD_REQUEST)
            technician.work_years = work_years
            changed.append("work_years")

        remove_avatar = to_bool(request.data.get("remove_avatar")) if "remove_avatar" in request.data else False
        remove_health_cert = to_bool(request.data.get("remove_health_cert")) if "remove_health_cert" in request.data else False

        avatar_file = request.FILES.get("avatar")
        if avatar_file:
            technician.avatar = avatar_file
            changed.append("avatar")
        elif remove_avatar and technician.avatar:
            technician.avatar.delete(save=False)
            technician.avatar = None
            changed.append("avatar")

        health_cert_file = request.FILES.get("health_cert")
        if health_cert_file:
            technician.health_cert = health_cert_file
            changed.append("health_cert")
        elif remove_health_cert and technician.health_cert:
            technician.health_cert.delete(save=False)
            technician.health_cert = None
            changed.append("health_cert")

        id_card_front_file = request.FILES.get("id_card_front")
        id_card_back_file = request.FILES.get("id_card_back")
        remove_id_card_front = to_bool(request.data.get("remove_id_card_front")) if "remove_id_card_front" in request.data else False
        remove_id_card_back = to_bool(request.data.get("remove_id_card_back")) if "remove_id_card_back" in request.data else False
        if id_card_front_file or id_card_back_file or remove_id_card_front or remove_id_card_back:
            verification = (
                technician.verifications.order_by("-submitted_at").first()
                or TechnicianVerification.objects.create(
                    technician=technician,
                    verification_type=TechnicianVerification.VerificationType.IDCARD,
                    status=TechnicianVerification.Status.PENDING,
                )
            )
            verify_changed = []
            if id_card_front_file:
                verification.id_card_front = id_card_front_file
                verify_changed.append("id_card_front")
            elif remove_id_card_front and verification.id_card_front:
                verification.id_card_front.delete(save=False)
                verification.id_card_front = None
                verify_changed.append("id_card_front")

            if id_card_back_file:
                verification.id_card_back = id_card_back_file
                verify_changed.append("id_card_back")
            elif remove_id_card_back and verification.id_card_back:
                verification.id_card_back.delete(save=False)
                verification.id_card_back = None
                verify_changed.append("id_card_back")

            if verify_changed:
                verification.save(update_fields=verify_changed)

        kept_license_urls = {str(x).strip() for x in request.data.getlist("kept_license_urls") if str(x).strip()}
        if "kept_license_urls" in request.data:
            for license_obj in technician.licenses.all():
                license_url = license_obj.license_file.url if license_obj.license_file else ""
                if license_url in kept_license_urls:
                    continue
                if license_obj.license_file:
                    license_obj.license_file.delete(save=False)
                license_obj.delete()

        max_license_files = 6
        existing_count = technician.licenses.count()
        remain = max(0, max_license_files - existing_count)
        for license_file in request.FILES.getlist("licenses")[:remain]:
            TechnicianLicense.objects.create(technician=technician, license_file=license_file)

        if changed:
            technician.save(update_fields=list(dict.fromkeys(changed + ["updated_at"])))
        return Response({"ok": True})

    def delete(self, request):
        """机构侧解绑（直接解除）"""
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        relation_id = request.data.get("relation_id") or request.query_params.get("relation_id")
        if not relation_id:
            return Response({"detail": "relation_id 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        relation = OrganizationTechnician.objects.filter(id=relation_id, organization=organization).first()
        if not relation:
            return Response({"detail": "绑定关系不存在"}, status=status.HTTP_404_NOT_FOUND)
        relation.status = OrganizationTechnician.Status.INACTIVE
        relation.save(update_fields=["status", "updated_at"])
        return Response({"ok": True, "status": relation.status})


class TechnicianUnbindOrganizationRequestView(APIView):
    """
    技师发起解绑申请（待机构确认）
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, relation_id: int):
        profile = TechnicianProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "仅技师可发起解绑申请"}, status=status.HTTP_403_FORBIDDEN)

        relation = OrganizationTechnician.objects.filter(id=relation_id, technician=profile).first()
        if not relation:
            return Response({"detail": "绑定关系不存在"}, status=status.HTTP_404_NOT_FOUND)
        if relation.status != OrganizationTechnician.Status.ACTIVE:
            return Response({"detail": "仅已绑定状态可申请解绑"}, status=status.HTTP_400_BAD_REQUEST)

        relation.status = OrganizationTechnician.Status.PENDING
        relation.save(update_fields=["status", "updated_at"])
        return Response({"ok": True, "status": relation.status, "detail": "已发起解绑申请，等待机构确认"})


class OrganizationDashboardView(APIView):
    """
    机构管理首页统计
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        relations = OrganizationTechnician.objects.filter(organization=organization)
        active_relations = relations.filter(status=OrganizationTechnician.Status.ACTIVE)
        pending_unbind_relations = relations.filter(status=OrganizationTechnician.Status.PENDING)

        active_technician_ids = list(active_relations.values_list("technician_id", flat=True))
        technician_qs = TechnicianProfile.objects.filter(id__in=active_technician_ids)

        listing_qs = Listing.objects.filter(technician_id__in=active_technician_ids, is_deleted=False)

        data = {
            "org": {
                "id": organization.id,
                "company_name": organization.company_name,
                "verification_status": organization.verification_status,
                "is_disabled": organization.is_disabled,
            },
            "overview": {
                "registered_users_total": technician_qs.count(),
                "technicians_total": relations.count(),
                "technicians_active": active_relations.count(),
                "technicians_pending_unbind": pending_unbind_relations.count(),
                "technicians_pending_verify": technician_qs.filter(
                    verification_status=TechnicianProfile.VerificationStatus.PENDING
                ).count(),
                "technicians_verified": technician_qs.filter(
                    verification_status=TechnicianProfile.VerificationStatus.APPROVED
                ).count(),
                "services_total": listing_qs.count(),
                "services_pending": listing_qs.filter(status=Listing.Status.PENDING).count(),
                "services_published": listing_qs.filter(status=Listing.Status.PUBLISHED).count(),
                "services_disabled": listing_qs.filter(status=Listing.Status.DISABLED).count(),
            },
            "todo": {
                "organization_verification_needed": organization.verification_status
                in [Organization.VerificationStatus.UNINITIATED, Organization.VerificationStatus.REJECTED],
                "pending_unbind_approvals": pending_unbind_relations.count(),
                "pending_technician_verifications": technician_qs.filter(
                    verification_status=TechnicianProfile.VerificationStatus.PENDING
                ).count(),
                "pending_service_audits": listing_qs.filter(status=Listing.Status.PENDING).count(),
            },
        }
        return Response(data)


class OrganizationMessagesView(APIView):
    """
    机构消息中心：审核与待办汇总
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        relation_qs = OrganizationTechnician.objects.filter(organization=organization).select_related("technician")
        pending_unbind_qs = relation_qs.filter(status=OrganizationTechnician.Status.PENDING)
        pending_unbind_count = pending_unbind_qs.count()
        pending_unbind = pending_unbind_qs.order_by("-updated_at")[:50]
        active_technician_ids = list(
            relation_qs.filter(status=OrganizationTechnician.Status.ACTIVE).values_list("technician_id", flat=True)
        )
        pending_technicians_qs = TechnicianProfile.objects.filter(
            id__in=active_technician_ids,
            verification_status=TechnicianProfile.VerificationStatus.PENDING,
        )
        pending_technician_verify_count = pending_technicians_qs.count()
        pending_technicians = pending_technicians_qs.order_by("-updated_at")[:50]
        pending_services_qs = Listing.objects.filter(
            technician_id__in=active_technician_ids,
            status=Listing.Status.PENDING,
            is_deleted=False,
        )
        pending_service_audit_count = pending_services_qs.count()
        pending_services = pending_services_qs.order_by("-updated_at")[:50]

        items = []
        if organization.verification_status in [
            Organization.VerificationStatus.UNINITIATED,
            Organization.VerificationStatus.REJECTED,
            Organization.VerificationStatus.PENDING,
        ]:
            items.append(
                {
                    "type": "organization_verification",
                    "level": "warning",
                    "title": "机构认证状态提醒",
                    "content": f"当前机构认证状态：{organization.verification_status}",
                    "action": "请在“我的认证”中补充资料并提交",
                }
            )

        for rel in pending_unbind:
            items.append(
                {
                    "type": "unbind_request",
                    "level": "warning",
                    "relation_id": rel.id,
                    "title": "技师解绑待处理",
                    "content": f"{rel.technician.real_name or '未命名'}（{rel.technician.phone or '-' }）发起解绑申请",
                    "action": "请在消息中心同意或拒绝",
                }
            )

        for tech in pending_technicians:
            items.append(
                {
                    "type": "technician_verify_pending",
                    "level": "info",
                    "technician_id": tech.id,
                    "title": "技师认证待审核",
                    "content": f"{tech.real_name or '未命名'} 的认证状态为待审核",
                    "action": "请到平台后台进行审核",
                }
            )

        for listing in pending_services:
            items.append(
                {
                    "type": "service_audit_pending",
                    "level": "info",
                    "listing_id": listing.id,
                    "title": "服务待审核",
                    "content": f"服务《{listing.title or '-'}》待平台审核",
                    "action": "可在服务管理中跟进",
                }
            )

        return Response(
            {
                "summary": {
                    "organization_status": organization.verification_status,
                    "pending_unbind_count": pending_unbind_count,
                    "pending_technician_verify_count": pending_technician_verify_count,
                    "pending_service_audit_count": pending_service_audit_count,
                    "total_messages": len(items),
                },
                "items": items,
            }
        )


class OrganizationServicesView(APIView):
    """
    机构服务管理（管理本机构已绑定技师发布的服务）
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        listing_id = (request.query_params.get("listing_id") or "").strip()
        if listing_id:
            active_technician_ids = get_org_active_technician_ids(organization)
            approved_technician_ids = list(
                TechnicianProfile.objects.filter(
                    id__in=active_technician_ids,
                    verification_status=TechnicianProfile.VerificationStatus.APPROVED,
                    is_disabled=False,
                ).values_list("id", flat=True)
            )
            listing = (
                Listing.objects.filter(id=listing_id, technician_id__in=approved_technician_ids, is_deleted=False)
                .select_related("technician", "category")
                .prefetch_related("audits", "services")
                .first()
            )
            if not listing:
                return Response({"detail": "服务不存在或不在机构管理范围内"}, status=status.HTTP_404_NOT_FOUND)
            return Response(organization_listing_detail_payload(listing))

        active_technician_ids = get_org_active_technician_ids(organization)
        status_val = (request.query_params.get("status") or "").strip()
        q = (request.query_params.get("q") or "").strip()
        try:
            page = max(1, int(request.query_params.get("page") or 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get("page_size") or 10)
            if page_size < 1:
                page_size = 10
            if page_size > 100:
                page_size = 100
        except (TypeError, ValueError):
            page_size = 10

        approved_technician_ids = list(
            TechnicianProfile.objects.filter(
                id__in=active_technician_ids,
                verification_status=TechnicianProfile.VerificationStatus.APPROVED,
                is_disabled=False,
            ).values_list("id", flat=True)
        )

        qs = Listing.objects.filter(technician_id__in=approved_technician_ids, is_deleted=False).select_related(
            "technician", "category"
        )
        if status_val:
            qs = qs.filter(status=status_val)
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(technician__real_name__icontains=q)
                | Q(contact_info__icontains=q)
            )

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = [
            {
                "id": x.id,
                "technician_id": x.technician_id,
                "real_name": x.technician.real_name if x.technician else "",
                "title": x.title,
                "status": x.status,
                "category_id": x.category_id,
                "category_name": x.category.name if x.category else "",
                "listing_price": str(x.listing_price) if x.listing_price is not None else None,
                "listing_price_unit": x.listing_price_unit,
                "service_areas": x.service_areas,
                "contact_info": x.contact_info,
                "cover_url": x.cover_url,
                "cover_urls": x.cover_urls,
                "updated_at": x.updated_at,
                "created_at": x.created_at,
            }
            for x in qs.order_by("-updated_at")[start:end]
        ]
        return Response(
            {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            }
        )

    def patch(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        listing_id = request.data.get("listing_id")
        if not listing_id:
            return Response({"detail": "listing_id 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        active_technician_ids = get_org_active_technician_ids(organization)
        approved_technician_ids = list(
            TechnicianProfile.objects.filter(
                id__in=active_technician_ids,
                verification_status=TechnicianProfile.VerificationStatus.APPROVED,
                is_disabled=False,
            ).values_list("id", flat=True)
        )
        listing = Listing.objects.filter(id=listing_id, technician_id__in=approved_technician_ids, is_deleted=False).first()
        if not listing:
            return Response({"detail": "服务不存在或不在机构管理范围内"}, status=status.HTTP_404_NOT_FOUND)

        if "category_id" in request.data:
            try:
                category_id = int(request.data.get("category_id"))
            except (TypeError, ValueError):
                return Response({"detail": "分类ID不合法"}, status=status.HTTP_400_BAD_REQUEST)
            category = Category.objects.filter(id=category_id).first()
            if not category:
                return Response({"detail": "分类不存在"}, status=status.HTTP_400_BAD_REQUEST)
            listing.category = category

        if "status" in request.data:
            status_val = str(request.data.get("status") or "").strip()
            if status_val not in {c[0] for c in Listing.Status.choices}:
                return Response({"detail": "服务状态参数不合法"}, status=status.HTTP_400_BAD_REQUEST)
            listing.status = status_val

        for field in ("title", "description", "service_areas", "contact_info", "listing_price_unit"):
            if field in request.data:
                setattr(listing, field, str(request.data.get(field) or "").strip())
        if "listing_price" in request.data:
            raw = request.data.get("listing_price")
            if raw in [None, ""]:
                listing.listing_price = None
            else:
                try:
                    listing.listing_price = Decimal(str(raw).strip())
                except (InvalidOperation, ValueError):
                    return Response({"detail": "服务价格格式不正确"}, status=status.HTTP_400_BAD_REQUEST)

        cover_image = request.FILES.get("cover_image")
        if cover_image:
            url = _org_save_upload_and_url(cover_image, "listings/covers")
            listing.cover_url = url
            listing.cover_urls = [url]

        kept_cover_urls = {str(x).strip() for x in request.data.getlist("kept_cover_urls") if str(x).strip()}
        if "kept_cover_urls" in request.data:
            existing_urls = [str(u).strip() for u in (listing.cover_urls or []) if str(u).strip()]
            listing.cover_urls = [u for u in existing_urls if u in kept_cover_urls]
            listing.cover_url = listing.cover_urls[0] if listing.cover_urls else ""

        cover_images = request.FILES.getlist("cover_images")
        if cover_images:
            urls = [_org_save_upload_and_url(img, "listings/covers") for img in cover_images]
            if urls:
                existing_urls = list(listing.cover_urls or [])
                remain = max(0, Listing.MAX_COVER_URLS - len(existing_urls))
                merged_urls = (existing_urls + urls[:remain])[: Listing.MAX_COVER_URLS]
                listing.cover_urls = merged_urls
                listing.cover_url = merged_urls[0] if merged_urls else ""

        listing.save()
        return Response({"ok": True})


class TechnicianOrganizationRelationListView(APIView):
    """
    技师查看自己与机构的绑定关系
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = TechnicianProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "仅技师可查看绑定关系"}, status=status.HTTP_403_FORBIDDEN)

        relations = (
            OrganizationTechnician.objects.filter(technician=profile)
            .select_related("organization")
            .order_by("-updated_at")
        )
        items = [
            {
                "relation_id": rel.id,
                "organization_id": rel.organization_id,
                "organization_name": rel.organization.company_name if rel.organization else "",
                "organization_phone": rel.organization.contact_phone if rel.organization else "",
                "status": rel.status,
                "updated_at": rel.updated_at,
            }
            for rel in relations
        ]
        return Response({"items": items, "total": len(items)})


class OrganizationTechnicianUnbindActionView(APIView):
    """
    机构同意/拒绝技师解绑
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, relation_id: int, action: str):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error
        relation = OrganizationTechnician.objects.filter(id=relation_id, organization=organization).first()
        if not relation:
            return Response({"detail": "绑定关系不存在"}, status=status.HTTP_404_NOT_FOUND)
        if relation.status != OrganizationTechnician.Status.PENDING:
            return Response({"detail": "当前不是待处理解绑状态"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "approve":
            relation.status = OrganizationTechnician.Status.INACTIVE
        elif action == "reject":
            relation.status = OrganizationTechnician.Status.ACTIVE
        else:
            return Response({"detail": "无效操作"}, status=status.HTTP_400_BAD_REQUEST)

        relation.save(update_fields=["status", "updated_at"])
        return Response({"ok": True, "status": relation.status})


class OrganizationTechnicianRegisterView(APIView):
    """
    机构代家政人员注册并提交认证资料
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @transaction.atomic
    def post(self, request):
        organization, error = get_user_organization_or_404(request.user)
        if error:
            return error

        if organization.is_disabled:
            return Response({"detail": "机构已被禁用"}, status=status.HTTP_403_FORBIDDEN)
        if organization.verification_status != Organization.VerificationStatus.APPROVED:
            return Response({"detail": "机构认证通过后才可新增技师"}, status=status.HTTP_400_BAD_REQUEST)

        phone = str(request.data.get("phone") or "").strip()
        password = str(request.data.get("password") or "")
        real_name = str(request.data.get("real_name") or "").strip()

        if not phone:
            return Response({"detail": "家政人员手机号不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        if not is_valid_mainland_phone(phone):
            return Response({"detail": "家政人员手机号格式不正确"}, status=status.HTTP_400_BAD_REQUEST)
        if not password or len(password) < 6:
            return Response({"detail": "密码长度不能少于6位"}, status=status.HTTP_400_BAD_REQUEST)
        if not real_name:
            return Response({"detail": "真实姓名不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        # 手机号全局唯一（技师和机构）
        if TechnicianProfile.objects.filter(phone=phone).exists() or Organization.objects.filter(contact_phone=phone).exists():
            return Response({"detail": "该手机号已注册"}, status=status.HTTP_400_BAD_REQUEST)

        username = generate_username(phone)
        user = User.objects.create(
            username=username,
            password=make_password(password),
            is_active=True,
            first_name=f"技师{phone[-4:]}「{real_name[:4]}」",
        )

        try:
            work_years = int(request.data.get("work_years") or 0)
        except (TypeError, ValueError):
            return Response({"detail": "工作年限必须为整数"}, status=status.HTTP_400_BAD_REQUEST)
        if work_years < 0:
            return Response({"detail": "工作年限不能小于0"}, status=status.HTTP_400_BAD_REQUEST)

        gender = str(request.data.get("gender") or "").strip()
        if gender and gender not in {c[0] for c in TechnicianProfile.Gender.choices}:
            return Response({"detail": "性别参数不合法"}, status=status.HTTP_400_BAD_REQUEST)

        profile = TechnicianProfile.objects.create(
            user=user,
            real_name=real_name,
            phone=phone,
            id_card_no=str(request.data.get("id_card_no") or "").strip(),
            gender=gender,
            service_types=str(request.data.get("service_types") or "").strip(),
            work_years=work_years,
            bio=str(request.data.get("bio") or "").strip(),
            service_areas=str(request.data.get("service_areas") or "").strip(),
            verification_status=TechnicianProfile.VerificationStatus.UNINITIATED,
        )

        # 可选上传：头像与健康证
        avatar_file = request.FILES.get("avatar")
        if avatar_file:
            profile.avatar = avatar_file
        health_cert_file = request.FILES.get("health_cert")
        if health_cert_file:
            profile.health_cert = health_cert_file
        if avatar_file or health_cert_file:
            profile.save(update_fields=["avatar", "health_cert", "updated_at"])

        id_card_front_file = request.FILES.get("id_card_front")
        id_card_back_file = request.FILES.get("id_card_back")
        license_files = request.FILES.getlist("licenses")

        # 提交认证：至少要有身份证正反面
        if not id_card_front_file or not id_card_back_file:
            return Response({"detail": "请上传身份证正反面以完成技师认证提交"}, status=status.HTTP_400_BAD_REQUEST)

        verification = TechnicianVerification.objects.create(
            technician=profile,
            verification_type=TechnicianVerification.VerificationType.IDCARD,
            id_card_front=id_card_front_file,
            id_card_back=id_card_back_file,
            health_cert=health_cert_file,
            status=TechnicianVerification.Status.PENDING,
        )
        _ = verification

        for license_file in license_files[:6]:
            TechnicianLicense.objects.create(technician=profile, license_file=license_file)

        # 机构代提交认证 -> 待审核
        profile.verification_status = TechnicianProfile.VerificationStatus.PENDING
        profile.save(update_fields=["verification_status", "updated_at"])

        return Response(
            {
                "ok": True,
                "technician_id": profile.id,
                "verification_status": profile.verification_status,
                "bind_hint": "认证通过后可调用 /api/accounts/organization/technicians 绑定到机构",
            },
            status=status.HTTP_201_CREATED,
        )
