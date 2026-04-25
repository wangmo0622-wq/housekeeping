from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import TechnicianProfile, TechnicianVerification
from catalog.models import ServiceType
from listings.models import Listing
from listings.serializers import (
    ListingCreateSerializer,
    ListingUpdateSerializer,
    listing_category_payload,
    service_price_display,
)


def _get_my_technician_profile(user):
    try:
        return TechnicianProfile.objects.get(user=user)
    except TechnicianProfile.DoesNotExist:
        return None


class TechnicianEnsureApproved(permissions.BasePermission):
    def has_permission(self, request, view):
        profile = _get_my_technician_profile(request.user)
        return bool(profile and profile.verification_status == TechnicianProfile.VerificationStatus.APPROVED and not profile.is_disabled)


class TechnicianProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "real_name": profile.real_name,
                "phone": profile.phone,
                "bio": profile.bio,
                "verification_status": profile.verification_status,
                "is_disabled": profile.is_disabled,
            }
        )

    def post(self, request):
        profile = _get_my_technician_profile(request.user)
        payload = request.data

        if not profile:
            profile = TechnicianProfile.objects.create(
                user=request.user,
                real_name=payload.get("real_name", ""),
                phone=payload.get("phone", ""),
                bio=payload.get("bio", ""),
                verification_status=TechnicianProfile.VerificationStatus.UNINITIATED,
            )
        else:
            profile.real_name = payload.get("real_name", profile.real_name)
            profile.phone = payload.get("phone", profile.phone)
            profile.bio = payload.get("bio", profile.bio)
            profile.save(update_fields=["real_name", "phone", "bio", "updated_at"])

        return Response({"ok": True})


class TechnicianUploadImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)

        if "image" not in request.FILES:
            return Response({"detail": "请选择要上传的图片"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES["image"]

        if not image_file.content_type.startswith('image/'):
            return Response({"detail": "只支持图片文件"}, status=status.HTTP_400_BAD_REQUEST)

        if image_file.size > 10 * 1024 * 1024:
            return Response({"detail": "图片大小不能超过10MB"}, status=status.HTTP_400_BAD_REQUEST)

        import os
        from django.conf import settings
        import uuid

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'listings', 'covers')
        os.makedirs(upload_dir, exist_ok=True)

        ext = os.path.splitext(image_file.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        file_url = f"{settings.MEDIA_URL}listings/covers/{filename}"

        return Response({
            "ok": True,
            "url": file_url
        }, status=status.HTTP_201_CREATED)


class TechnicianVerificationStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({
                "is_technician": False,
                "technician_id": None,
                "verification_status": None,
                "message": "未申请技师认证",
            })

        latest_verification = TechnicianVerification.objects.filter(
            technician=profile
        ).order_by("-submitted_at").first()

        def get_file_url(field):
            if field and hasattr(field, 'url'):
                return field.url
            return None

        service_types_info = []
        if profile.service_types:
            service_type_ids = [s.strip() for s in profile.service_types.split(',') if s.strip()]
            if service_type_ids:
                from catalog.models import ServiceType
                services = ServiceType.objects.filter(id__in=service_type_ids, status=ServiceType.Status.ENABLED)
                service_types_info = [{
                    "id": s.id,
                    "name": s.name,
                    "category_id": s.category_id,
                    "category_name": s.category.name if s.category else None,
                    "base_price": float(s.base_price),
                    "price_unit": s.price_unit
                } for s in services]

        verifications = list(TechnicianVerification.objects.filter(
            technician=profile
        ).values(
            "id", "verification_type", "status", "submitted_at", "reviewed_at", "admin_note"
        ).order_by("-submitted_at")[:10])

        return Response({
            "is_technician": True,
            "technician_id": profile.id,
            "verification_status": profile.verification_status,
            "is_disabled": profile.is_disabled,
            "real_name": profile.real_name,
            "phone": profile.phone,
            "id_card_no": profile.id_card_no,
            "gender": profile.gender,
            "age": profile.age,
            "bio": profile.bio,
            "service_types": profile.service_types,
            "service_types_info": service_types_info,
            "work_years": profile.work_years,
            "avatar": get_file_url(profile.avatar),
            "latest_verification": {
                "id": latest_verification.id,
                "status": latest_verification.status,
                "submitted_at": latest_verification.submitted_at,
                "verification_type": latest_verification.verification_type,
                "id_card_front": get_file_url(latest_verification.id_card_front),
                "id_card_back": get_file_url(latest_verification.id_card_back),
                "licenses": [get_file_url(license.license_file) for license in profile.licenses.all()],
            } if latest_verification else None,
            "verification_history": verifications,
        })


class TechnicianSubmitVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = _get_my_technician_profile(request.user)

        real_name = request.data.get("real_name")
        phone = request.data.get("phone")
        id_card_no = request.data.get("id_card_no")
        gender = request.data.get("gender", "")
        service_types_str = request.data.get("service_types", "")
        work_years = request.data.get("work_years", 0)
        bio = request.data.get("bio", "")

        if not real_name or not phone:
            return Response({"detail": "姓名和手机号必填"}, status=status.HTTP_400_BAD_REQUEST)

        if not profile:
            profile = TechnicianProfile.objects.create(
                user=request.user,
                real_name=real_name,
                phone=phone,
                id_card_no=id_card_no or "",
                gender=gender if gender in [TechnicianProfile.Gender.MALE, TechnicianProfile.Gender.FEMALE] else "",
                service_types=service_types_str,
                work_years=int(work_years) if work_years else 0,
                bio=bio,
                verification_status=TechnicianProfile.VerificationStatus.PENDING,
            )
        else:
            if profile.verification_status == TechnicianProfile.VerificationStatus.APPROVED:
                return Response({"detail": "已认证通过，无需重复提交"}, status=status.HTTP_400_BAD_REQUEST)

            profile.real_name = real_name
            profile.phone = phone
            profile.id_card_no = id_card_no or ""
            profile.gender = gender if gender in [TechnicianProfile.Gender.MALE, TechnicianProfile.Gender.FEMALE] else ""
            profile.service_types = service_types_str
            profile.work_years = int(work_years) if work_years else 0
            profile.bio = bio

        avatar = request.FILES.get("avatar")
        if avatar:
            profile.avatar = avatar

        health_cert = request.FILES.get("health_cert")
        if health_cert:
            profile.health_cert = health_cert

        pending_verification = TechnicianVerification.objects.filter(
            technician=profile,
            status=TechnicianVerification.Status.PENDING
        ).order_by("-submitted_at").first()

        id_card_front = request.FILES.get("id_card_front")
        id_card_back = request.FILES.get("id_card_back")
        license_files = request.FILES.getlist("license_files")

        # 处理清空执照文件的请求
        clear_license_files = request.data.get("clear_license_files", False)
        if isinstance(clear_license_files, str):
            clear_license_files = clear_license_files.lower() == "true"
        
        if clear_license_files:
            from accounts.models import TechnicianLicense
            # 清空当前技师的所有执照文件
            TechnicianLicense.objects.filter(technician=profile).delete()

        if pending_verification:
            if id_card_front:
                pending_verification.id_card_front = id_card_front
            if id_card_back:
                pending_verification.id_card_back = id_card_back
            if health_cert:
                pending_verification.health_cert = health_cert
            pending_verification.save()
            verification_id = pending_verification.id
        else:
            verification_type = request.data.get("verification_type", TechnicianVerification.VerificationType.OTHER)
            v = TechnicianVerification.objects.create(
                technician=profile,
                verification_type=verification_type,
                id_card_front=id_card_front,
                id_card_back=id_card_back,
                health_cert=health_cert,
                status=TechnicianVerification.Status.PENDING,
            )
            verification_id = v.id

        # 处理多个执照文件
        if license_files:
            from accounts.models import TechnicianLicense
            
            # 检查执照文件数量限制（最多6个）
            current_license_count = profile.licenses.count()
            new_license_count = len(license_files)
            total_count = current_license_count + new_license_count
            
            if total_count > 6:
                return Response({
                    "detail": f"执照文件数量超过限制，最多只能上传6个，当前已有{current_license_count}个"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            for license_file in license_files:
                TechnicianLicense.objects.create(
                    technician=profile,
                    license_file=license_file
                )

        if profile.verification_status != TechnicianProfile.VerificationStatus.PENDING:
            profile.verification_status = TechnicianProfile.VerificationStatus.PENDING
        profile.save()

        return Response({
            "ok": True,
            "verification_id": verification_id,
            "verification_status": profile.verification_status,
        }, status=status.HTTP_201_CREATED)


class TechnicianMyListingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class _Paginator(PageNumberPagination):
        page_size_query_param = "page_size"

    def get(self, request):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)

        qs = Listing.objects.filter(technician=profile, is_deleted=False).prefetch_related("services", "audits").order_by("-created_at")

        paginator = self._Paginator()
        page = paginator.paginate_queryset(qs, request, view=self)
        items = [
            {
                "id": x.id,
                "title": x.title,
                "category_id": listing_category_payload(x)["primary_category_id"],
                "category_name": listing_category_payload(x)["primary_category_name"],
                "category_path": listing_category_payload(x)["category_path"],
                "primary_category_id": listing_category_payload(x)["primary_category_id"],
                "primary_category_name": listing_category_payload(x)["primary_category_name"],
                "secondary_category_id": listing_category_payload(x)["secondary_category_id"],
                "secondary_category_name": listing_category_payload(x)["secondary_category_name"],
                "secondary_categories": listing_category_payload(x)["secondary_categories"],
                "status": x.status,
                "cover_url": x.cover_url,
                "cover_urls": list(x.cover_urls)[: Listing.MAX_COVER_URLS]
                if x.cover_urls
                else ([x.cover_url] if x.cover_url else []),
                "listing_price": str(x.listing_price) if x.listing_price is not None else None,
                "listing_price_unit": x.listing_price_unit or "次",
                "service_price": service_price_display(x),
                "description": x.description,
                "created_at": x.created_at,
                "published_at": x.published_at,
                "audit_note": x.audit_note,
                "service_areas": x.service_areas,
                "contact_info": x.contact_info,
                "audits": [
                    {
                        "id": a.id,
                        "status": a.status,
                        "audit_note": a.audit_note,
                        "reviewed_at": a.reviewed_at,
                        "reviewed_by": a.reviewed_by.username if a.reviewed_by else None,
                        "created_at": a.created_at,
                    }
                    for a in x.audits.all().order_by("-created_at")
                ],
            }
            for x in page
        ]
        return paginator.get_paginated_response(items)

    def post(self, request):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)

        if profile.is_disabled:
            return Response({"detail": "账号已禁用"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ListingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vd = serializer.validated_data
        listing = Listing(
            technician=profile,
            category_id=vd["category_id"],
            title=vd["title"],
            description=vd.get("description", ""),
            cover_url=vd.get("cover_url", ""),
            cover_urls=vd.get("cover_urls") or [],
            listing_price=vd.get("listing_price"),
            listing_price_unit=(vd.get("listing_price_unit") or "次"),
            service_areas=vd.get("service_areas", ""),
            contact_info=vd.get("contact_info", ""),
            status=Listing.Status.PENDING,
        )
        listing.save()
        
        from listings.models import ListingAudit
        ListingAudit.objects.create(
            listing=listing,
            status=ListingAudit.Status.PENDING
        )
        
        return Response({"ok": True, "listing_id": listing.id}, status=status.HTTP_201_CREATED)


class TechnicianUpdateListingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, listing_id: int):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)
        if profile.is_disabled:
            return Response({"detail": "账号已禁用"}, status=status.HTTP_403_FORBIDDEN)

        listing = get_object_or_404(Listing, id=listing_id, technician=profile, is_deleted=False)
        if listing.status not in [Listing.Status.DRAFT, Listing.Status.REJECTED, Listing.Status.PENDING]:
            return Response({"detail": "发布状态已锁定"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ListingUpdateSerializer(listing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            if field == "category_id":
                listing.category_id = value
            else:
                setattr(listing, field, value)

        listing.status = Listing.Status.PENDING
        listing.save()
        
        from listings.models import ListingAudit
        ListingAudit.objects.create(
            listing=listing,
            status=ListingAudit.Status.PENDING
        )
        
        return Response({"ok": True})


class TechnicianDeleteListingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, listing_id: int):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)
        if profile.is_disabled:
            return Response({"detail": "账号已禁用"}, status=status.HTTP_403_FORBIDDEN)
        if profile.verification_status != TechnicianProfile.VerificationStatus.APPROVED:
            return Response({"detail": "仅认证通过的技师可删除服务"}, status=status.HTTP_403_FORBIDDEN)

        listing = get_object_or_404(Listing, id=listing_id, technician=profile, is_deleted=False)
        listing.is_deleted = True
        listing.save()
        return Response({"ok": True})


class TechnicianToggleListingStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, listing_id: int):
        profile = _get_my_technician_profile(request.user)
        if not profile:
            return Response({"detail": "未找到技师信息"}, status=status.HTTP_404_NOT_FOUND)
        if profile.is_disabled:
            return Response({"detail": "账号已禁用"}, status=status.HTTP_403_FORBIDDEN)
        if profile.verification_status != TechnicianProfile.VerificationStatus.APPROVED:
            return Response({"detail": "仅认证通过的技师可上架/下架服务"}, status=status.HTTP_403_FORBIDDEN)

        listing = get_object_or_404(Listing, id=listing_id, technician=profile, is_deleted=False)
        if listing.status not in [Listing.Status.PUBLISHED, Listing.Status.DISABLED]:
            return Response({"detail": "只能对已发布或下架的服务进行操作"}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get("action")
        if action == "disable":
            listing.status = Listing.Status.DISABLED
        elif action == "enable":
            listing.status = Listing.Status.PUBLISHED
        else:
            return Response({"detail": "无效的操作"}, status=status.HTTP_400_BAD_REQUEST)

        listing.save()
        return Response({"ok": True, "status": listing.status})
