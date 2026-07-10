from rest_framework import generics
from .models import SportCategory, Sport, Gym, GymPrice
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from math import radians, sin, cos, sqrt, atan2
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from gym.models import Gym
from gym.serializers import GymSerializer
from subscriptions.models import UserSubscription


class SportCategoryListView(generics.ListAPIView):
    queryset = SportCategory.objects.all()
    serializer_class = SportCategorySerializer


class SportListView(generics.ListAPIView):
    queryset = Sport.objects.all()
    serializer_class = SportSerializer


class GymListView(generics.ListAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer


class GymPriceListView(generics.ListAPIView):
    queryset = GymPrice.objects.all()
    serializer_class = GymPriceSerializer


class TopPopularGymsAPIView(APIView):
    def get(self, request):
        gyms = Gym.objects.filter(is_popular=True).order_by("-popularity_score")[:5]
        serializer = GymSerializer(gyms, many=True)
        return Response(serializer.data)
    


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


class NearbyGymsAPIView(APIView):
    """
    نزدیک‌ترین باشگاه‌های مجاز اشتراک فعال کاربر
    GET /api/gym/nearby/?lat=...&lon=...
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="lat",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="عرض جغرافیایی موقعیت کاربر",
            ),
            OpenApiParameter(
                name="lon",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="طول جغرافیایی موقعیت کاربر",
            ),
        ],
        responses={200: GymSerializer(many=True)},
        summary="نزدیک‌ترین باشگاه‌های مجاز اشتراک فعال",
    )
    def get(self, request):
        try:
            user_lat = float(request.query_params.get("lat"))
            user_lon = float(request.query_params.get("lon"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "پارامترهای lat و lon الزامی و باید عددی باشند."},
                status=400
            )

        subscription = (
            UserSubscription.objects
            .filter(
                user=request.user,
                status="active",
                end_date__gt=timezone.now(),
            )
            .select_related("plan")
            .prefetch_related("plan__gyms")
            .order_by("-created_at")
            .first()
        )

        if not subscription or not subscription.is_active:
            return Response(
                {"detail": "اشتراک فعالی یافت نشد."},
                status=404
            )

        gyms = list(subscription.plan.gyms.all())

        if not gyms:
            return Response(
                {"detail": "باشگاهی برای این اشتراک تعریف نشده است."},
                status=404
            )

        sorted_gyms = sorted(
            gyms,
            key=lambda g: calculate_distance(user_lat, user_lon, g.latitude, g.longitude)
        )[:10]

        serializer = GymSerializer(sorted_gyms, many=True)

        return Response(serializer.data)
     

class GymDetailAPIView(generics.RetrieveAPIView):
    queryset = Gym.objects.prefetch_related(
        "sports",
        "facilities",
        "prices",
        "images",
        "videos",
        "banners",
        "coaches",
        "reviews",
    )

    serializer_class = GymDetailSerializer