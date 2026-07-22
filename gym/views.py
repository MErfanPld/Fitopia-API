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
    

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status

from .models import Gym, Sport, GymCoach
from subscriptions.models import UserSubscription
from .serializers import SportAccessSerializer, GymSummarySerializer, CoachSerializer

def _get_active_subscription_for_user(user):
    now = timezone.now()
    return UserSubscription.objects.filter(user=user, end_date__gt=now).first()

class GymSportsAccessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, gym_id):
        gym = get_object_or_404(Gym, pk=gym_id)
        user = request.user if request.user.is_authenticated else None

        active_sub = None
        allowed_sport_ids = set()
        belongs_to_gym = False

        if user:
            active_sub = _get_active_subscription_for_user(user)
            if active_sub:
                # try subscription -> sports
                if hasattr(active_sub, 'sports') and active_sub.sports.exists():
                    allowed_sport_ids = set(active_sub.sports.values_list('id', flat=True))
                # or plan -> allowed_sports
                elif hasattr(active_sub, 'plan') and hasattr(active_sub.plan, 'sports'):
                    allowed_sport_ids = set(active_sub.plan.sports.values_list('id', flat=True))
                # check if subscription explicitly tied to gyms
                if hasattr(active_sub, 'gyms'):
                    belongs_to_gym = gym.id in list(active_sub.gyms.values_list('id', flat=True))
                else:
                    # fallback policy: subscription applies to gyms in subscriptionGyms service or global
                    belongs_to_gym = True

        # Build sports list
        sports_qs = gym.sports.all()  # adjust relation name
        sports_list = []
        for s in sports_qs:
            has_access = False
            if active_sub and belongs_to_gym:
                if not allowed_sport_ids:
                    # policy: subscription covers all sports of gym if no explicit sport list
                    has_access = True
                else:
                    has_access = s.id in allowed_sport_ids
            sports_list.append({
                'id': s.id,
                'name': s.name,
                'has_access': has_access
            })

        subscription_info = None
        if active_sub:
            subscription_info = {
                'id': active_sub.id,
                # 'is_active': active_sub.is_active,
                'end_date': active_sub.end_date,
                'gyms': list(active_sub.gyms.values_list('id', flat=True)) if hasattr(active_sub, 'gyms') else [],
            }

        return Response({
            'gym': GymSummarySerializer(gym).data,
            'sports': sports_list,
            'subscription': subscription_info
        }, status=status.HTTP_200_OK)


class SportCoachesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id, sport_id):
        gym = get_object_or_404(Gym, pk=gym_id)
        sport = get_object_or_404(Sport, pk=sport_id)

        # verify sport belongs to gym
        if not gym.sports.filter(pk=sport.id).exists():
            return Response({'detail': 'Sport not available for this gym'}, status=status.HTTP_404_NOT_FOUND)

        # verify user subscription & access
        user = request.user
        active_sub = _get_active_subscription_for_user(user)
        if not active_sub:
            return Response({'detail': 'No active subscription'}, status=status.HTTP_403_FORBIDDEN)

        # determine allowed_sport_ids as above
        allowed_sport_ids = set()
        if hasattr(active_sub, 'sports') and active_sub.sports.exists():
            allowed_sport_ids = set(active_sub.sports.values_list('id', flat=True))
        elif hasattr(active_sub, 'plan') and hasattr(active_sub.plan, 'sports'):
            allowed_sport_ids = set(active_sub.plan.sports.values_list('id', flat=True))

        belongs_to_gym = True
        if hasattr(active_sub, 'gyms'):
            belongs_to_gym = gym.id in list(active_sub.gyms.values_list('id', flat=True))

        allowed = False
        if belongs_to_gym:
            if not allowed_sport_ids:
                allowed = True
            else:
                allowed = sport.id in allowed_sport_ids

        if not allowed:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        coaches = GymCoach.objects.filter(gym=gym, sports__id=sport.id).distinct()
        serializer = CoachSerializer(coaches, many=True)
        return Response({'sport': {'id': sport.id, 'name': sport.name}, 'coaches': serializer.data})