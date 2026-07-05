from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import UserSubscription
from .serializers import SubscriptionGymsSerializer

from .models import Plan, UserSubscription, UserDiscountProfile
from .serializers import (
    PlanSerializer,
    PlanDetailSerializer,
    UserSubscriptionSerializer,
    PurchaseSubscriptionSerializer,
    UserDiscountProfileSerializer,
)


class PlanListView(generics.ListAPIView):
    """لیست پلن‌های فعال"""
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).prefetch_related("gyms")


class PlanDetailView(generics.RetrieveAPIView):
    """جزئیات یک پلن به همراه باشگاه‌های مجاز"""
    serializer_class = PlanDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).prefetch_related("gyms")



class PurchaseSubscriptionView(views.APIView):
    """خرید اشتراک"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="PurchaseRequest",
            fields={
                "plan_id": drf_serializers.IntegerField(help_text="آیدی پلن"),
                "use_discount": drf_serializers.BooleanField(default=False, help_text="استفاده از تخفیف"),
            }
        ),
        responses={201: UserSubscriptionSerializer},
        summary="خرید اشتراک",
    )
    def post(self, request):
        serializer = PurchaseSubscriptionSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        plan = get_object_or_404(
            Plan,
            id=serializer.validated_data["plan_id"],
            is_active=True
        )
        use_discount = serializer.validated_data["use_discount"]

        discount_amount = 0
        if use_discount:
            try:
                discount_profile = request.user.discount_profile
                if discount_profile.discount_amount > 0 and not discount_profile.is_used:
                    discount_amount = min(discount_profile.discount_amount, plan.price)
            except UserDiscountProfile.DoesNotExist:
                pass

        final_price = plan.price - discount_amount

        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            paid_amount=final_price,
            discount_applied=discount_amount,
        )

        if discount_amount > 0:
            request.user.discount_profile.use_discount()

        return Response(
            {
                "message": "اشتراک با موفقیت خریداری شد.",
                "subscription": UserSubscriptionSerializer(subscription).data,
                "discount_applied": discount_amount,
                "final_price": final_price,
            },
            status=status.HTTP_201_CREATED,
        )


class MySubscriptionView(views.APIView):
    """اشتراک فعال کاربر"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status="active",
            end_date__gt=timezone.now(),
        ).select_related("plan").first()

        if not subscription:
            return Response(
                {"message": "اشتراک فعالی ندارید."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(UserSubscriptionSerializer(subscription).data)


class MySubscriptionHistoryView(generics.ListAPIView):
    """تاریخچه اشتراک‌های کاربر"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSubscription.objects.filter(
            user=self.request.user
        ).select_related("plan").order_by("-created_at")


class MyDiscountView(views.APIView):
    """وضعیت تخفیف کاربر"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.discount_profile
            serializer = UserDiscountProfileSerializer(profile)
            return Response(serializer.data)
        except UserDiscountProfile.DoesNotExist:
            return Response(
                {
                    "accumulated_leftover_tokens": 0,
                    "discount_amount": 0,
                    "is_used": False,
                }
            )


class ExpireSubscriptionView(views.APIView):
    """
    انقضای دستی اشتراک (برای تست یا ادمین)
    در پروداکشن این کار رو Celery beat انجام میده
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        subscription = get_object_or_404(UserSubscription, pk=pk)
        subscription.expire()
        return Response({"message": "اشتراک منقضی شد و توکن‌های باقیمانده ذخیره شدند."})
    
    
class SubscriptionGymsAPIView(APIView):
    """
    برگرداندن باشگاه‌های مجاز یک اشتراک خاص
    GET /api/subscriptions/<pk>/gyms/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        subscription = get_object_or_404(
            UserSubscription.objects.select_related("plan").prefetch_related("plan__gyms"),
            pk=pk
        )

        # فقط صاحب اشتراک یا ادمین اجازه دسترسی داره
        if subscription.user_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied("شما به این اشتراک دسترسی ندارید.")

        serializer = SubscriptionGymsSerializer(subscription)
        return Response(serializer.data)
    
    
class MyActiveSubscriptionGymsAPIView(APIView):
    """
    GET /api/subscriptions/me/gyms/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = (
            UserSubscription.objects
            .filter(user=request.user, status="active")
            .select_related("plan")
            .prefetch_related("plan__gyms")
            .order_by("-created_at")
            .first()
        )
        if not subscription:
            return Response({"detail": "اشتراک فعالی یافت نشد."}, status=404)

        serializer = SubscriptionGymsSerializer(subscription)
        return Response(serializer.data)