from rest_framework import views, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers

from .models import GymToken
from .serializers import (
    GymTokenSerializer,
    RequestGymTokenSerializer,
    ValidateGymTokenSerializer,
)


class RequestGymTokenView(views.APIView):
    """
    درخواست توکن روزانه برای یک باشگاه.
    یک توکن با اعتبار ۲۴ ساعته صادر میشه و یک توکن از اشتراک کسر میشه.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="RequestTokenInput",
            fields={
                "gym_id": drf_serializers.IntegerField(help_text="آیدی باشگاه"),
            }
        ),
        responses={201: GymTokenSerializer},
        summary="دریافت توکن روزانه باشگاه",
    )
    def post(self, request):
        serializer = RequestGymTokenSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        subscription = serializer.validated_data["subscription"]
        gym_id = serializer.validated_data["gym_id"]

        # صدور توکن
        token = GymToken.objects.create(
            subscription=subscription,
            gym_id=gym_id,
        )

        # کسر یک توکن از اشتراک
        subscription.tokens_used += 1
        subscription.save(update_fields=["tokens_used"])

        return Response(
            {
                "message": "توکن با موفقیت صادر شد.",
                "token": GymTokenSerializer(token).data,
                "tokens_remaining": subscription.tokens_remaining,
            },
            status=status.HTTP_201_CREATED,
        )


class ValidateGymTokenView(views.APIView):
    """
    اعتبارسنجی توکن توسط باشگاه.
    باشگاه کد توکن رو اسکن میکنه و این endpoint تایید میکنه.
    بعد از تایید توکن مصرف‌شده میشه.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="ValidateTokenInput",
            fields={
                "token_code": drf_serializers.UUIDField(help_text="کد توکن (UUID)"),
            }
        ),
        responses={200: GymTokenSerializer},
        summary="اعتبارسنجی و مصرف توکن (توسط باشگاه)",
    )
    def post(self, request):
        serializer = ValidateGymTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_code = serializer.validated_data["token_code"]

        try:
            token = GymToken.objects.select_related(
                "subscription__user", "gym"
            ).get(token_code=token_code)
        except GymToken.DoesNotExist:
            return Response(
                {"message": "توکن یافت نشد.", "valid": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not token.is_valid:
            return Response(
                {
                    "message": "توکن منقضی یا قبلاً استفاده‌شده است.",
                    "valid": False,
                    "status": token.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token.use()

        return Response(
            {
                "message": "ورود تایید شد.",
                "valid": True,
                "token": GymTokenSerializer(token).data,
            }
        )


class MyGymTokensView(generics.ListAPIView):
    """لیست توکن‌های کاربر"""
    serializer_class = GymTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GymToken.objects.filter(
            subscription__user=self.request.user
        ).select_related("gym", "subscription__user").order_by("-issued_at")


class MyActiveTokensView(generics.ListAPIView):
    """توکن‌های فعال کاربر"""
    serializer_class = GymTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GymToken.objects.filter(
            subscription__user=self.request.user,
            status="active",
            valid_until__gt=timezone.now(),
        ).select_related("gym", "subscription__user")