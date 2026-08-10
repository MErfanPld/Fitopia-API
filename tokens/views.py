from django.db import transaction
from django.utils import timezone

from rest_framework import views, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from gym_panel.permissions import IsGymStaff, has_gym_access

from .models import GymToken
from .serializers import (
    GymTokenSerializer,
    RequestGymTokenSerializer,
    ValidateGymTokenSerializer,
)


class RequestGymTokenView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="RequestTokenInput",
            fields={
                "gym_id": drf_serializers.IntegerField(help_text="آیدی باشگاه"),
            },
        ),
        responses={201: GymTokenSerializer},
        summary="دریافت توکن روزانه باشگاه",
    )
    def post(self, request):
        serializer = RequestGymTokenSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        subscription = serializer.validated_data["subscription"]
        gym_id = serializer.validated_data["gym_id"]

        with transaction.atomic():
            from subscriptions.models import UserSubscription

            locked_sub = (
                UserSubscription.objects.select_for_update()
                .get(pk=subscription.pk)
            )
            if locked_sub.tokens_remaining <= 0:
                return Response(
                    {"message": "توکن‌های اشتراک شما تمام شده است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if locked_sub.status != "active" or locked_sub.end_date <= timezone.now():
                return Response(
                    {"message": "اشتراک فعالی ندارید."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing = GymToken.objects.filter(
                subscription=locked_sub,
                gym_id=gym_id,
                status="active",
                valid_until__gt=timezone.now(),
            ).exists()
            if existing:
                return Response(
                    {
                        "message": (
                            "شما یک توکن فعال برای این باشگاه دارید. "
                            "ابتدا آن را استفاده کنید."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = GymToken.objects.create(
                subscription=locked_sub,
                gym_id=gym_id,
            )
            locked_sub.tokens_used += 1
            locked_sub.save(update_fields=["tokens_used"])

        return Response(
            {
                "message": "توکن با موفقیت صادر شد.",
                "token": GymTokenSerializer(token).data,
                "tokens_remaining": locked_sub.tokens_remaining,
            },
            status=status.HTTP_201_CREATED,
        )


class ValidateGymTokenView(views.APIView):
    permission_classes = [IsGymStaff]

    @extend_schema(
        request=inline_serializer(
            name="ValidateTokenInput",
            fields={
                "token_code": drf_serializers.UUIDField(help_text="کد توکن (UUID)"),
            },
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

        if not has_gym_access(request.user, token.gym_id):
            return Response(
                {"message": "شما به این باشگاه دسترسی ندارید.", "valid": False},
                status=status.HTTP_403_FORBIDDEN,
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

        consumed = token.use()
        if not consumed:
            return Response(
                {
                    "message": "توکن منقضی یا قبلاً استفاده‌شده است.",
                    "valid": False,
                    "status": token.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token.refresh_from_db()
        return Response(
            {
                "message": "ورود تایید شد.",
                "valid": True,
                "token": GymTokenSerializer(token).data,
            }
        )


class MyGymTokensView(generics.ListAPIView):
    serializer_class = GymTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            GymToken.objects.filter(subscription__user=self.request.user)
            .select_related("gym", "subscription__user")
            .order_by("-issued_at")
        )


class MyActiveTokensView(generics.ListAPIView):
    serializer_class = GymTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GymToken.objects.filter(
            subscription__user=self.request.user,
            status="active",
            valid_until__gt=timezone.now(),
        ).select_related("gym", "subscription__user")
