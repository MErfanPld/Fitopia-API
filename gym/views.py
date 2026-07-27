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
# CALCULATE DISTANCE
# =========================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate distance between two coordinates
    using Haversine formula.

    Result: kilometers
    """

    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


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
            "plan__sports",
        )
        .order_by("-created_at")
        .first()
    )


# =========================================================
# NEARBY GYMS
# =========================================================

class NearbyGymsAPIView(APIView):

    """
    نزدیک‌ترین باشگاه‌های مجاز اشتراک فعال کاربر

    GET:
    /api/gym/nearby/?lat=35.7&lon=51.4
    """

    permission_classes = [
        IsAuthenticated
    ]

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
        responses={
            200: GymSerializer(many=True)
        },
        summary="نزدیک‌ترین باشگاه‌های مجاز اشتراک فعال",
    )
    def get(self, request):

        # -----------------------------------------
        # Get coordinates
        # -----------------------------------------

        try:

            user_lat = float(
                request.query_params.get("lat")
            )

            user_lon = float(
                request.query_params.get("lon")
            )

        except (
            TypeError,
            ValueError
        ):

            return Response(
                {
                    "detail": (
                        "پارامترهای lat و lon "
                        "الزامی و باید عددی باشند."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------------
        # Get active subscription
        # -----------------------------------------

        subscription = (
            _get_active_subscription_for_user(
                request.user
            )
        )

        if not subscription:

            return Response(
                {
                    "detail": "اشتراک فعالی یافت نشد."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # -----------------------------------------
        # Check plan
        # -----------------------------------------

        if not subscription.plan:

            return Response(
                {
                    "detail": (
                        "اشتراک شما فاقد پلن معتبر است."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # -----------------------------------------
        # Get gyms from plan
        # -----------------------------------------

        gyms = list(
            subscription.plan.gyms.all()
        )

        if not gyms:

            return Response(
                {
                    "detail": (
                        "باشگاهی برای این اشتراک "
                        "تعریف نشده است."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # -----------------------------------------
        # Sort gyms by distance
        # -----------------------------------------

        sorted_gyms = sorted(
            gyms,
            key=lambda gym: calculate_distance(
                user_lat,
                user_lon,
                gym.latitude,
                gym.longitude
            )
        )[:10]

        # -----------------------------------------
        # Serialize
        # -----------------------------------------

        serializer = GymSerializer(
            sorted_gyms,
            many=True
        )

        return Response(
            serializer.data,
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

        # -----------------------------------------
        # Get gym
        # -----------------------------------------

        gym = get_object_or_404(
            Gym,
            pk=gym_id
        )

        # -----------------------------------------
        # Default values
        # -----------------------------------------

        active_sub = None

        allowed_sport_ids = set()

        belongs_to_gym = False

        # -----------------------------------------
        # Check authenticated user
        # -----------------------------------------

        if (
            request.user
            and request.user.is_authenticated
        ):

            active_sub = (
                _get_active_subscription_for_user(
                    request.user
                )
            )

        # -----------------------------------------
        # Check subscription
        # -----------------------------------------

        if (
            active_sub
            and active_sub.plan
        ):

            # -------------------------------------
            # Check gym access
            # -------------------------------------

            belongs_to_gym = (
                active_sub.plan.gyms
                .filter(
                    id=gym.id
                )
                .exists()
            )

            # -------------------------------------
            # Get allowed sports
            # -------------------------------------

            allowed_sport_ids = set(
                active_sub.plan.sports
                .values_list(
                    "id",
                    flat=True
                )
            )

        # -----------------------------------------
        # Build sports response
        # -----------------------------------------

        sports_list = []

        sports_qs = (
            gym.sports.all()
        )

        for sport in sports_qs:

            has_access = False

            # User has active subscription
            # and subscription includes this gym

            if (
                active_sub
                and belongs_to_gym
            ):

                # If plan has no specific sports,
                # all gym sports are accessible

                if not allowed_sport_ids:

                    has_access = True

                else:

                    has_access = (
                        sport.id
                        in allowed_sport_ids
                    )

            sports_list.append(
                {
                    "id": sport.id,
                    "name": sport.name,
                    "has_access": has_access,
                }
            )

        # -----------------------------------------
        # Subscription info
        # -----------------------------------------

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

        # -----------------------------------------
        # Response
        # -----------------------------------------

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

        # -----------------------------------------
        # Get gym
        # -----------------------------------------

        gym = get_object_or_404(
            Gym,
            pk=gym_id
        )

        # -----------------------------------------
        # Get sport
        # -----------------------------------------

        sport = get_object_or_404(
            Sport,
            pk=sport_id
        )

        # -----------------------------------------
        # Check sport belongs to gym
        # -----------------------------------------

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

        # -----------------------------------------
        # Get active subscription
        # -----------------------------------------

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

        # -----------------------------------------
        # Check plan
        # -----------------------------------------

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

        # -----------------------------------------
        # Check gym access
        # -----------------------------------------

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

        # -----------------------------------------
        # Check sport access
        # -----------------------------------------

        allowed_sport_ids = set(
            active_sub.plan.sports
            .values_list(
                "id",
                flat=True
            )
        )

        # If plan has specific sports,
        # check current sport

        if (
            allowed_sport_ids
            and sport.id
            not in allowed_sport_ids
        ):

            return Response(
                {
                    "detail": (
                        "شما به این رشته ورزشی "
                        "دسترسی ندارید."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # -----------------------------------------
        # Get coaches
        # -----------------------------------------

        coaches = (
            GymCoach.objects
            .filter(
                gym=gym,
                sports=sport
            )
            .distinct()
        )

        # -----------------------------------------
        # Serialize coaches
        # -----------------------------------------

        serializer = CoachSerializer(
            coaches,
            many=True
        )

        # -----------------------------------------
        # Response
        # -----------------------------------------

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