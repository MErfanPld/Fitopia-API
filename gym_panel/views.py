from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from users.models import User
from users.serializers import UserSerializer
from gym.models import Gym, GymPrice

from .serializers import (
    GymPanelLoginSerializer,
    GymStaffAccessSerializer,
    GymPanelUpdateSerializer,
    FieldEditRequestSerializer,
    SuggestNewSportSerializer,
    GymChangeRequestSerializer,
    GymPriceSerializer,
)
from .models import GymStaffAccess, GymChangeRequest
from .permissions import IsGymStaff, has_gym_access


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _get_gym_or_403(user, gym_id):
    if not has_gym_access(user, gym_id):
        raise PermissionDenied("شما به این باشگاه دسترسی ندارید.")
    return get_object_or_404(Gym, id=gym_id)


# =========================
# 🔐 AUTH
# =========================
@extend_schema(tags=["gym-panel"])
class GymPanelLoginView(GenericAPIView):
    serializer_class = GymPanelLoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=GymPanelLoginSerializer,
        responses={200: GymStaffAccessSerializer(many=True)},
        summary="لاگین پنل باشگاه‌دار",
        tags=["gym-panel"],
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(username=username, is_staff_user=True)
        except User.DoesNotExist:
            return Response(
                {"error": "نام کاربری یا رمز اشتباه است"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"error": "نام کاربری یا رمز اشتباه است"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "حساب غیرفعال است"},
                status=status.HTTP_403_FORBIDDEN,
            )

        accesses = GymStaffAccess.objects.filter(user=user).select_related("gym")

        return Response({
            "tokens": get_tokens(user),
            "user": UserSerializer(user).data,
            "gyms": GymStaffAccessSerializer(accesses, many=True).data,
        })


@extend_schema(tags=["gym-panel"])
class MyGymsView(generics.ListAPIView):
    serializer_class = GymStaffAccessSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        return GymStaffAccess.objects.filter(
            user=self.request.user
        ).select_related("gym")


# =========================
# ✏️ ویرایش آزاد اطلاعات باشگاه
# =========================
class GymPanelUpdateView(GenericAPIView):
    serializer_class = GymPanelUpdateSerializer
    permission_classes = [IsGymStaff]

    @extend_schema(
        request=GymPanelUpdateSerializer,
        responses={200: GymPanelUpdateSerializer},
        summary="ویرایش آزاد اطلاعات باشگاه",
        tags=["gym-panel"],
    )
    def patch(self, request, gym_id):
        gym = _get_gym_or_403(request.user, gym_id)
        serializer = self.get_serializer(gym, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# =========================
# 🎫 تیکت برای فیلدهای محدود (name/address/lat/long)
# =========================
class GymFieldEditRequestView(GenericAPIView):
    serializer_class = FieldEditRequestSerializer
    permission_classes = [IsGymStaff]

    @extend_schema(
        request=FieldEditRequestSerializer,
        responses={201: GymChangeRequestSerializer},
        summary="ثبت تیکت برای ویرایش فیلد محدود (نام/آدرس/موقعیت)",
        tags=["gym-panel"],
    )
    def post(self, request, gym_id):
        gym = _get_gym_or_403(request.user, gym_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_request = GymChangeRequest.objects.create(
            gym=gym,
            requested_by=request.user,
            request_type="field_edit",
            payload=serializer.validated_data,
        )
        return Response(
            {
                "message": "درخواست ثبت شد و منتظر تایید ادمین است.",
                "request": GymChangeRequestSerializer(change_request).data,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================
# 🆕 پیشنهاد رشته‌ی ورزشی جدید
# =========================
class SuggestNewSportView(GenericAPIView):
    serializer_class = SuggestNewSportSerializer
    permission_classes = [IsGymStaff]

    @extend_schema(
        request=SuggestNewSportSerializer,
        responses={201: GymChangeRequestSerializer},
        summary="پیشنهاد رشته‌ی ورزشی جدید",
        tags=["gym-panel"],
    )
    def post(self, request, gym_id):
        gym = _get_gym_or_403(request.user, gym_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_request = GymChangeRequest.objects.create(
            gym=gym,
            requested_by=request.user,
            request_type="new_sport",
            payload=serializer.validated_data,
        )
        return Response(
            {
                "message": "پیشنهاد ثبت شد و منتظر تایید ادمین است.",
                "request": GymChangeRequestSerializer(change_request).data,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================
# 📋 لیست تیکت‌های خودم
# =========================
@extend_schema(tags=["gym-panel"])
class MyChangeRequestsView(generics.ListAPIView):
    serializer_class = GymChangeRequestSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymChangeRequest.objects.filter(gym_id=gym_id)


# =========================
# 💰 مدیریت رشته‌های موجود باشگاه (GymPrice) — آزاد
# =========================
@extend_schema(tags=["gym-panel"])
class GymPriceListCreateView(generics.ListCreateAPIView):
    serializer_class = GymPriceSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymPrice.objects.filter(gym_id=gym_id).select_related("sport")

    def perform_create(self, serializer):
        gym_id = self.kwargs["gym_id"]
        gym = _get_gym_or_403(self.request.user, gym_id)
        sport = serializer.validated_data["sport"]

        if GymPrice.objects.filter(gym=gym, sport=sport).exists():
            raise drf_serializers.ValidationError(
                "قیمت این رشته قبلاً ثبت شده؛ آن را ویرایش کنید."
            )

        serializer.save(gym=gym)
        gym.sports.add(sport)


@extend_schema(tags=["gym-panel"])
class GymPriceUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GymPriceSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymPrice.objects.filter(gym_id=gym_id)

    def perform_destroy(self, instance):
        gym = instance.gym
        sport = instance.sport
        instance.delete()
        gym.sports.remove(sport)
        
        
from gym.models import Gym, GymPrice, GymCoach
from .serializers import GymCoachSerializer


@extend_schema(tags=["gym-panel"])
class GymCoachListCreateView(generics.ListCreateAPIView):
    serializer_class = GymCoachSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymCoach.objects.filter(gym_id=gym_id).prefetch_related("sports")

    def perform_create(self, serializer):
        gym_id = self.kwargs["gym_id"]
        gym = _get_gym_or_403(self.request.user, gym_id)
        serializer.save(gym=gym)


@extend_schema(tags=["gym-panel"])
class GymCoachUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GymCoachSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymCoach.objects.filter(gym_id=gym_id)
    
    
from .serializers import GymTicketMessageCreateSerializer, GymTicketMessageSerializer
from .models import GymTicketMessage


@extend_schema(tags=["gym-panel"])
class TicketDetailView(generics.RetrieveAPIView):
    """جزئیات کامل یک تیکت + کل تاریخچه پیام‌ها"""
    serializer_class = GymChangeRequestSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymChangeRequest.objects.filter(gym_id=gym_id).prefetch_related("messages")


class TicketMessageCreateView(GenericAPIView):
    """باشگاه‌دار روی تیکتش پیام/پاسخ می‌فرسته"""
    serializer_class = GymTicketMessageCreateSerializer
    permission_classes = [IsGymStaff]

    @extend_schema(
        request=GymTicketMessageCreateSerializer,
        responses={201: GymTicketMessageSerializer},
        summary="ارسال پیام روی تیکت (توسط باشگاه‌دار)",
        tags=["gym-panel"],
    )
    def post(self, request, gym_id, ticket_id):
        _get_gym_or_403(request.user, gym_id)
        ticket = get_object_or_404(GymChangeRequest, id=ticket_id, gym_id=gym_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        msg = GymTicketMessage.objects.create(
            ticket=ticket,
            sender_role="gym",
            sender=request.user,
            message=serializer.validated_data["message"],
        )
        return Response(GymTicketMessageSerializer(msg).data, status=status.HTTP_201_CREATED)
    

from .models import GymCustomer
from .serializers import GymCustomerSerializer


@extend_schema(tags=["gym-panel"])
class GymCustomerListCreateView(generics.ListCreateAPIView):
    serializer_class = GymCustomerSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        qs = GymCustomer.objects.filter(gym_id=gym_id).select_related("sport")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                models.Q(full_name__icontains=search) | models.Q(phone__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        gym_id = self.kwargs["gym_id"]
        gym = _get_gym_or_403(self.request.user, gym_id)
        serializer.save(gym=gym)


@extend_schema(tags=["gym-panel"])
class GymCustomerUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GymCustomerSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _get_gym_or_403(self.request.user, gym_id)
        return GymCustomer.objects.filter(gym_id=gym_id)