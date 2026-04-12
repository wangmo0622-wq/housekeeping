import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import re
import random

import requests

# 配置日志
logger = logging.getLogger(__name__)


def generate_username(phone):
    """
    生成用户名：前缀 + 手机尾4位 + 1位随机数字
    例如：用户_68923
    """
    prefix = "用户_"
    phone_last4 = phone[-4:]
    random_digit = random.randint(0, 9)
    return f"{prefix}{phone_last4}{random_digit}"


class MiniProgramUserSerializer:
    @staticmethod
    def get_user_info(user):
        from accounts.models import TechnicianProfile
        phone = None
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

        return {
            "id": user.id,
            "username": user.username,
            "phone": phone,
            "is_technician": is_technician,
            "technician_status": technician_status,
            "technician_id": technician_id,
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
    退出登录：让 refresh token 失效
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
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
