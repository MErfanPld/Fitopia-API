from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Gym, Sport, GymReview
from .serializers import GymReviewCreateSerializer, GymReviewSerializer


class SportScheduleView(APIView):
    """برنامه زمانی یک رشته در باشگاه (روز / ساعت / جنسیت)."""

    permission_classes = [AllowAny]

    def get(self, request, gym_id, sport_id):
        gym = get_object_or_404(Gym, pk=gym_id)
        sport = get_object_or_404(Sport, pk=sport_id)

        if not gym.sports.filter(pk=sport.id).exists():
            return Response(
                {"detail": "این رشته ورزشی در این باشگاه وجود ندارد."},
                status=status.HTTP_404_NOT_FOUND,
            )

        day_names = {
            0: "شنبه",
            1: "یکشنبه",
            2: "دوشنبه",
            3: "سه‌شنبه",
            4: "چهارشنبه",
            5: "پنجشنبه",
            6: "جمعه",
        }

        schedules = []
        gender_restriction = "all"
        offering = None
        try:
            from gym_panel.expansion_models import GymOffering
            offering = (
                GymOffering.objects
                .filter(gym=gym, sport=sport, is_active=True)
                .prefetch_related("schedules")
                .first()
            )
        except Exception:
            offering = None

        if offering:
            gender_restriction = offering.gender_restriction
            for s in offering.schedules.all():
                schedules.append({
                    "day_of_week": s.day_of_week,
                    "day_name": day_names.get(s.day_of_week, str(s.day_of_week)),
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "gender_restriction": gender_restriction,
                })

        return Response(
            {
                "gym": {"id": gym.id, "name": gym.name},
                "sport": {"id": sport.id, "name": sport.name},
                "gender_restriction": gender_restriction,
                "schedules": schedules,
            },
            status=status.HTTP_200_OK,
        )


class GymReviewCreateView(APIView):
    """ثبت نظر برای باشگاه."""

    permission_classes = [IsAuthenticated]

    def post(self, request, gym_id):
        gym = get_object_or_404(Gym, pk=gym_id)
        serializer = GymReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        name = (
            getattr(user, "full_name", None)
            or getattr(user, "username", None)
            or "کاربر"
        )
        review = GymReview.objects.create(
            gym=gym,
            name=str(name)[:100],
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data["comment"],
        )
        return Response(
            GymReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )
