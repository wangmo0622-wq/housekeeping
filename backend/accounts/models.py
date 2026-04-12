from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class TechnicianProfile(models.Model):
    """
    技师个人资料（认证结果由 verification_status 控制）。
    公共端门禁逻辑依赖：
    - verification_status == approved
    - is_disabled == False
    """

    class VerificationStatus(models.TextChoices):
        UNINITIATED = "uninitiated", "未发起认证"
        PENDING = "pending", "待审核"
        APPROVED = "approved", "通过"
        REJECTED = "rejected", "未通过"

    class Gender(models.TextChoices):
        MALE = "male", "男"
        FEMALE = "female", "女"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="technician_profile")

    real_name = models.CharField(max_length=64, blank=True, verbose_name="真实姓名")
    phone = models.CharField(max_length=32, verbose_name="联系电话")
    id_card_no = models.CharField(max_length=32, blank=True, verbose_name="身份证号")
    gender = models.CharField(
        max_length=8,
        choices=Gender.choices,
        blank=True,
        verbose_name="性别",
        help_text="用户选择的性别",
    )
    service_types = models.CharField(max_length=256, blank=True, verbose_name="服务类型")
    work_years = models.IntegerField(default=0, verbose_name="工作年限")
    health_cert = models.FileField(upload_to="verification/health/", blank=True, null=True, verbose_name="健康证")
    avatar = models.FileField(upload_to="verification/avatar/", blank=True, null=True, verbose_name="形象照片")
    bio = models.TextField(blank=True, verbose_name="简介")
    service_areas = models.TextField(
        blank=True,
        verbose_name="服务区域",
        help_text="可服务区域，多选，以逗号分隔",
    )

    # 认证结果
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNINITIATED,
        verbose_name="认证状态",
    )
    is_disabled = models.BooleanField(
        default=False, verbose_name="禁用", help_text="禁用：公共端等同未通过，直接 404"
    )
    is_recommended = models.BooleanField(
        default=False, verbose_name="推荐", help_text="推荐技师，优先展示"
    )
    recommended_at = models.DateTimeField(
        null=True, blank=True, verbose_name="推荐时间"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_age_from_id_card(self):
        """根据身份证号计算年龄"""
        if not self.id_card_no or len(self.id_card_no) not in [15, 18]:
            return None
        
        try:
            if len(self.id_card_no) == 18:
                birth_year = int(self.id_card_no[6:10])
                birth_month = int(self.id_card_no[10:12])
                birth_day = int(self.id_card_no[12:14])
            else:  # 15位身份证
                birth_year = 1900 + int(self.id_card_no[6:8])
                birth_month = int(self.id_card_no[8:10])
                birth_day = int(self.id_card_no[10:12])
            
            today = datetime.today()
            age = today.year - birth_year
            
            # 如果今年生日还没到，年龄减1
            if (today.month, today.day) < (birth_month, birth_day):
                age -= 1
            
            return max(0, age)
        except (ValueError, IndexError):
            return None

    @property
    def age(self):
        """年龄属性"""
        return self.calculate_age_from_id_card()

    def __str__(self) -> str:
        return f"TechnicianProfile<{self.user_id}>"

    class Meta:
        verbose_name = "技师"
        verbose_name_plural = "技师"


class TechnicianLicense(models.Model):
    """
    技师执照文件（支持多个执照）
    """
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="licenses"
    )
    license_file = models.FileField(
        upload_to="verification/license/", verbose_name="执照文件"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    def __str__(self) -> str:
        return f"TechnicianLicense<{self.technician_id}>"

    class Meta:
        verbose_name = "技师执照"
        verbose_name_plural = "技师执照"
        ordering = ["-uploaded_at"]


class TechnicianVerification(models.Model):
    """
    技师认证材料与审核过程（可保留历史）。
    """

    class VerificationType(models.TextChoices):
        IDCARD = "idcard", "身份证"
        HEALTH = "health", "健康证"
        LICENSE = "license", "从业资质"
        CRIMINAL = "criminal", "无犯罪记录"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "通过"
        REJECTED = "rejected", "驳回"

    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="verifications"
    )
    verification_type = models.CharField(
        max_length=16,
        choices=VerificationType.choices,
        default=VerificationType.OTHER,
        verbose_name="认证类型",
    )

    id_card_front = models.FileField(
        upload_to="verification/idcard/front/", blank=True, null=True, verbose_name="身份证正面"
    )
    id_card_back = models.FileField(
        upload_to="verification/idcard/back/", blank=True, null=True, verbose_name="身份证反面"
    )
    health_cert = models.FileField(
        upload_to="verification/health/", blank=True, null=True, verbose_name="健康证"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, verbose_name="审核状态")
    admin_note = models.TextField(blank=True, verbose_name="审核意见")
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="审核时间")
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="审核人")

    def __str__(self) -> str:
        return f"TechnicianVerification<{self.technician_id}:{self.status}>"

    class Meta:
        verbose_name = "技师认证记录"
        verbose_name_plural = "技师认证记录"

