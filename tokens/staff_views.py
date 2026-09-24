"""
APIهای باشگاه‌دار برای بررسی و تایید ورود با توکن کاربر.

جریان پیشنهادی:
1) lookup  → فقط بررسی اعتبار و نمایش مشخصات کاربر (بدون مصرف توکن)
2) admit   → تایید ورود، مصرف توکن، ثبت حضور، انقضا (used)
"""
from django.utils import timezone
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers

from gym_panel.permissions import has_gym_access, user_has_perm
from gym_panel.models import GymVisit

from .models import GymToken
from .serializers import GymTokenSerializer


def _token_user_payload(token):
    user = token.subscription.user if token.subscription_id else None
    if not user:
        return None
    return {
        "id": user.id,
        "full_name": user.full_name or user.username or "",
        "phone_number": user.phone_number or "",
        "username": user.username or "",
    }


def _expires_in_seconds(token):
    if not token.valid_until:
        return 0
    delta = token.valid_until - timezone.now()
    return max(int(delta.total_seconds()), 0)


def _find_active_token(token_code):
    code = str(token_code).strip()
    return (
        GymToken.objects.select_related(
            "subscription__user", "subscription__plan", "gym"
        )
        .filter(token_code=code, status="active")
        .order_by("-issued_at")
        .first()
    )


def _resolve_for_gym(token, gym_id):
    """
    بررسی سازگاری توکن با باشگاه اسکن‌کننده.
    برمی‌گرداند: (ok, error_response_or_None, target_gym_id)
    """
    gym_id = int(gym_id)

    if token.gym_id is not None:
        if int(token.gym_id) != gym_id:
            return (
                False,
                Response(
                    {
                        "valid": False,
                        "can_admit": False,
                        "message": "این توکن مخصوص باشگاه دیگری است.",
                        "token_gym_id": token.gym_id,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                ),
                token.gym_id,
            )
        return True, None, gym_id

    # بلیت سراسری
    plan = token.subscription.plan if token.subscription_id else None
    if not plan or not plan.gyms.filter(id=gym_id).exists():
        return (
            False,
            Response(
                {
                    "valid": False,
                    "can_admit": False,
                    "message": "این باشگاه در پلن اشتراک کاربر نیست.",
                },
                status=status.HTTP_403_FORBIDDEN,
            ),
            gym_id,
        )
    return True, None, gym_id


def _staff_may_handle_tokens(user, gym_id):
    if not has_gym_access(user, gym_id):
        return False
    # owner یا هر نقش با حضور
    return user_has_perm(user, gym_id, "attendance.create") or has_gym_access(
        user, gym_id
    )


class GymTokenLookupView(views.APIView):
    """بررسی توکن بدون مصرف — فقط نمایش اعتبار و مشخصات کاربر."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="GymTokenLookupInput",
            fields={
                "token_code": drf_serializers.CharField(help_text="کد ۵رقمی کاربر"),
            },
        ),
        summary="باشگاه‌دار: بررسی توکن کاربر (بدون ورود)",
    )
    def post(self, request, gym_id):
        if not _staff_may_handle_tokens(request.user, gym_id):
            return Response(
                {"message": "شما به این باشگاه دسترسی ندارید."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token_code = str(request.data.get("token_code", "")).strip()
        if not token_code.isdigit() or len(token_code) != 5:
            return Response(
                {
                    "valid": False,
                    "can_admit": False,
                    "message": "کد توکن باید دقیقاً ۵ رقم باشد.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = _find_active_token(token_code)
        if token is None:
            # ممکن است used یا expired باشد — برای پیام بهتر
            any_tok = (
                GymToken.objects.filter(token_code=token_code)
                .order_by("-issued_at")
                .first()
            )
            if any_tok is None:
                return Response(
                    {
                        "valid": False,
                        "can_admit": False,
                        "message": "توکن یافت نشد.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {
                    "valid": False,
                    "can_admit": False,
                    "message": "توکن منقضی یا قبلاً استفاده‌شده است.",
                    "status": any_tok.status,
                    "used_at": any_tok.used_at,
                    "valid_until": any_tok.valid_until,
                    "user": _token_user_payload(any_tok),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok, err, _ = _resolve_for_gym(token, gym_id)
        if not ok:
            return err

        is_still_valid = token.is_valid
        return Response(
            {
                "valid": is_still_valid,
                "can_admit": is_still_valid,
                "message": "توکن معتبر است." if is_still_valid else "توکن منقضی شده.",
                "token_code": token.token_code,
                "status": token.status,
                "is_universal": token.gym_id is None,
                "gym_id": token.gym_id,
                "issued_at": token.issued_at,
                "valid_until": token.valid_until,
                "expires_in_seconds": _expires_in_seconds(token),
                "user": _token_user_payload(token),
            }
        )


class GymTokenAdmitView(views.APIView):
    """تایید ورود: مصرف توکن + ثبت حضور + وضعیت used."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="GymTokenAdmitInput",
            fields={
                "token_code": drf_serializers.CharField(help_text="کد ۵رقمی کاربر"),
            },
        ),
        summary="باشگاه‌دار: تایید ورود و مصرف توکن",
    )
    def post(self, request, gym_id):
        if not _staff_may_handle_tokens(request.user, gym_id):
            return Response(
                {"message": "شما به این باشگاه دسترسی ندارید."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token_code = str(request.data.get("token_code", "")).strip()
        if not token_code.isdigit() or len(token_code) != 5:
            return Response(
                {
                    "valid": False,
                    "message": "کد توکن باید دقیقاً ۵ رقم باشد.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = _find_active_token(token_code)
        if token is None:
            return Response(
                {
                    "valid": False,
                    "message": "توکن یافت نشد یا قبلاً مصرف شده است.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        ok, err, target_gym_id = _resolve_for_gym(token, gym_id)
        if not ok:
            return err

        if not token.is_valid:
            return Response(
                {
                    "valid": False,
                    "message": "توکن منقضی یا غیرفعال است.",
                    "status": token.status,
                    "valid_until": token.valid_until,
                    "user": _token_user_payload(token),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # بلیت سراسری را به باشگاه محل اسکن قفل کن
        if token.gym_id is None:
            GymToken.objects.filter(pk=token.pk).update(gym_id=target_gym_id)
            token.gym_id = target_gym_id
            token.refresh_from_db()

        consumed = token.use()
        if not consumed:
            return Response(
                {
                    "valid": False,
                    "message": "توکن منقضی یا قبلاً استفاده‌شده است.",
                    "status": token.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token.refresh_from_db()
        visit = (
            GymVisit.objects.filter(token=token)
            .order_by("-created_at")
            .first()
        )

        return Response(
            {
                "valid": True,
                "message": "ورود تایید شد. توکن مصرف و منقضی شد.",
                "token": GymTokenSerializer(token).data,
                "user": _token_user_payload(token),
                "visit_id": visit.id if visit else None,
                "used_at": token.used_at,
            }
        )


class GymTokenTodayAdmissionsView(views.APIView):
    """لیست ورودهای امروز این باشگاه که با توکن ثبت شده‌اند."""

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="باشگاه‌دار: ورودهای امروز با توکن")
    def get(self, request, gym_id):
        if not has_gym_access(request.user, gym_id):
            return Response(
                {"message": "شما به این باشگاه دسترسی ندارید."},
                status=status.HTTP_403_FORBIDDEN,
            )

        today = timezone.localdate()
        visits = (
            GymVisit.objects.filter(
                gym_id=gym_id,
                source="token",
                created_at__date=today,
            )
            .select_related("token__subscription__user", "customer")
            .order_by("-created_at")[:100]
        )

        results = []
        for v in visits:
            user_data = None
            if v.token_id and v.token.subscription_id:
                user_data = _token_user_payload(v.token)
            results.append(
                {
                    "visit_id": v.id,
                    "token_code": v.token.token_code if v.token_id else None,
                    "used_at": v.token.used_at if v.token_id else v.created_at,
                    "check_in_at": v.check_in_at or v.created_at,
                    "user": user_data,
                    "guest_name": v.guest_name or "",
                }
            )

        return Response({"date": str(today), "count": len(results), "results": results})
