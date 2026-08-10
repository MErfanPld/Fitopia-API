from math import radians, sin, cos, sqrt, atan2

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import SportCategory, Sport, Gym, GymPrice, GymCoach
from .serializers import (
    SportCategorySerializer,
    SportSerializer,
    GymSerializer,
    GymPriceSerializer,
    GymDetailSerializer,
    GymSummarySerializer,
    CoachSerializer,
)

from subscriptions.models import UserSubscription


# =========================================================
# SPORT CATEGORY
# =========================================================

class SportCategoryListView(generics.ListAPIView):
    queryset = SportCategory.objects.all()
    serializer_class = SportCategorySerializer


# =========================================================
# SPORT LIST
# =========================================================

class SportListView(generics.ListAPIView):
    queryset = Sport.objects.all()
    serializer_class = SportSerializer


# =========================================================
# GYM LIST
# =========================================================

class GymListView(generics.ListAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer


# =========================================================
# GYM PRICE LIST
# =========================================================

class GymPriceListView(generics.ListAPIView):
    queryset = GymPrice.objects.all()
    serializer_class = GymPriceSerializer


# =========================================================
# TOP POPULAR GYMS
# =========================================================

class TopPopularGymsAPIView(APIView):

    def get(self, request):

        gyms = (
            Gym.objects
            .filter(is_popular=True)
            .order_by("-popularity_score")[:5]
        )

        serializer = GymSerializer(
            gyms,
            many=True
        )

        return Response(serializer.data)


# =========================================================
# GET ACTIVE SUBSCRIPTION
# =========================================================

def _get_active_subscription_for_user(user):

    return (
        UserSubscription.objects
        .filter(
            user=user,
            status="active",
            end_date__gt=timezone.now(),
        )
        .select_related("plan")
        .prefetch_related(
            "plan__gyms",
        )
        .order_by("-created_at")
        .first()
    )


# =========================================================
# NEARBY GYMS
# =========================================================

from math import radians, sin, cos, sqrt, atan2

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from subscriptions.models import UserSubscription

from .models import Gym
from .serializers import GymSerializer


def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371.0

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


class NearbyGymsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            user_lat = float(
                request.query_params.get("lat")
            )

            user_lon = float(
                request.query_params.get("lon")
            )

        except (TypeError, ValueError):

            return Response(
                {
                    "detail": "lat و lon الزامی و باید عدد باشند."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            radius = float(
                request.query_params.get(
                    "radius",
                    10
                )
            )

        except (TypeError, ValueError):

            radius = 10

        gyms = Gym.objects.all()

        subscription = (
            UserSubscription.objects
            .filter(
                user=request.user,
                status="active",
                end_date__gt=timezone.now()
            )
            .select_related("plan")
            .prefetch_related("plan__gyms")
            .order_by("-created_at")
            .first()
        )

        allowed_gym_ids = set()

        if subscription and subscription.plan:

            allowed_gym_ids = set(
                subscription.plan.gyms.values_list(
                    "id",
                    flat=True
                )
            )

        nearby_gyms = []

        for gym in gyms:

            if (
                gym.latitude is None
                or gym.longitude is None
            ):
                continue

            try:

                gym_lat = float(
                    gym.latitude
                )

                gym_lon = float(
                    gym.longitude
                )

            except (TypeError, ValueError):

                continue

            distance = calculate_distance(
                user_lat,
                user_lon,
                gym_lat,
                gym_lon
            )

            if distance <= radius:

                nearby_gyms.append(
                    {
                        "gym": gym,
                        "distance": round(
                            distance,
                            3
                        ),
                        "has_access": (
                            gym.id
                            in allowed_gym_ids
                        )
                    }
                )

        nearby_gyms.sort(
            key=lambda item: item["distance"]
        )

        results = []

        for item in nearby_gyms:

            gym = item["gym"]

            serializer = GymSerializer(
                gym,
                context={
                    "request": request
                }
            )

            gym_data = serializer.data

            gym_data["distance_km"] = (
                item["distance"]
            )

            gym_data["has_access"] = (
                item["has_access"]
            )

            results.append(
                gym_data
            )

        return Response(
            results,
            status=status.HTTP_200_OK
        )


# =========================================================
# GYM DETAIL
# =========================================================

class GymDetailAPIView(
    generics.RetrieveAPIView
):

    queryset = (
        Gym.objects
        .prefetch_related(
            "sports",
            "facilities",
            "prices",
            "images",
            "videos",
            "banners",
            "coaches",
            "reviews",
        )
    )

    serializer_class = GymDetailSerializer


# =========================================================
# GYM SPORTS ACCESS
# =========================================================

class GymSportsAccessView(APIView):

    """
    نمایش رشته‌های ورزشی یک باشگاه
    و مشخص کردن دسترسی کاربر به هر رشته.

    Public endpoint:
    کاربر بدون لاگین هم می‌تواند لیست ورزش‌ها را ببیند.

    اگر کاربر اشتراک فعال داشته باشد:
    has_access = true / false
    """

    permission_classes = [
        AllowAny
    ]

    def get(
        self,
        request,
        gym_id
    ):

        gym = get_object_or_404(
            Gym,
            pk=gym_id
        )

        active_sub = None

        belongs_to_gym = False

        if (
            request.user
            and request.user.is_authenticated
        ):

            active_sub = (
                _get_active_subscription_for_user(
                    request.user
                )
            )

        if (
            active_sub
            and active_sub.plan
        ):

            belongs_to_gym = (
                active_sub.plan.gyms
                .filter(
                    id=gym.id
                )
                .exists()
            )

        # Access is determined at gym level via plan.gyms.
        # Plan has no sport-level restriction in the current schema,
        # so if the user has access to the gym, all of its sports are accessible.

        sports_list = []

        sports_qs = (
            gym.sports.all()
        )

        for sport in sports_qs:

            has_access = bool(
                active_sub
                and belongs_to_gym
            )

            sports_list.append(
                {
                    "id": sport.id,
                    "name": sport.name,
                    "has_access": has_access,
                }
            )

        subscription_info = None

        if active_sub:

            subscription_info = {
                "id": active_sub.id,

                "status": active_sub.status,

                "start_date": (
                    active_sub.start_date
                ),

                "end_date": (
                    active_sub.end_date
                ),

                "gym_access": (
                    belongs_to_gym
                ),

                "plan": (
                    active_sub.plan.id
                    if active_sub.plan
                    else None
                ),
            }

        return Response(
            {
                "gym": (
                    GymSummarySerializer(
                        gym
                    ).data
                ),

                "sports": sports_list,

                "subscription": (
                    subscription_info
                ),
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# SPORT COACHES
# =========================================================

class SportCoachesView(APIView):

    """
    دریافت مربیان یک رشته ورزشی
    در یک باشگاه.

    فقط کاربران دارای اشتراک فعال
    و دسترسی به باشگاه و رشته می‌توانند
    مربیان را ببینند.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        gym_id,
        sport_id
    ):

        gym = get_object_or_404(
            Gym,
            pk=gym_id
        )

        sport = get_object_or_404(
            Sport,
            pk=sport_id
        )

        if not gym.sports.filter(
            pk=sport.id
        ).exists():

            return Response(
                {
                    "detail": (
                        "این رشته ورزشی "
                        "در این باشگاه وجود ندارد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        active_sub = (
            _get_active_subscription_for_user(
                request.user
            )
        )

        if not active_sub:

            return Response(
                {
                    "detail": (
                        "اشتراک فعالی ندارید."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if not active_sub.plan:

            return Response(
                {
                    "detail": (
                        "اشتراک شما "
                        "فاقد پلن معتبر است."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        belongs_to_gym = (
            active_sub.plan.gyms
            .filter(
                id=gym.id
            )
            .exists()
        )

        if not belongs_to_gym:

            return Response(
                {
                    "detail": (
                        "شما به این باشگاه "
                        "دسترسی ندارید."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Sport-level access:
        # Current Plan model only restricts by gym (plan.gyms).
        # If the user has gym access, they may view coaches for any
        # sport offered by that gym.

        coaches = (
            GymCoach.objects
            .filter(
                gym=gym,
                sports=sport
            )
            .distinct()
        )

        serializer = CoachSerializer(
            coaches,
            many=True
        )

        return Response(
            {
                "sport": {
                    "id": sport.id,
                    "name": sport.name,
                },

                "coaches": serializer.data,
            },
            status=status.HTTP_200_OK
        )
