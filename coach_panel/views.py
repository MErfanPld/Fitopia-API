"""پنل مربی — ثبت تمرین، PR، بانک حرکات، پیشرفت، لیدربورد، شبکه اجتماعی"""
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone

from rest_framework import generics, views
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from gym_panel.permissions import IsGymStaff
from gym_panel.coach_models import CoachStudent, CoachPost, StudentMonthlyStat
from gym_panel.coach_serializers import (
    CoachProfileSerializer,
    CoachProfileUpdateSerializer,
    CoachPostSerializer,
    CoachPostCreateSerializer,
)

from .permissions import IsCoachOnly, ensure_coach
from .models import (
    Exercise,
    WorkoutSession,
    PersonalRecord,
    ProgressPhoto,
    FeedLike,
    FeedComment,
)
from .serializers import (
    ExerciseSerializer,
    WorkoutSessionSerializer,
    WorkoutSessionWriteSerializer,
    PersonalRecordSerializer,
    ProgressPhotoSerializer,
    FeedCommentSerializer,
)


class CoachMeView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        coach = ensure_coach(request.user, request.query_params.get("gym_id"))
        return Response(CoachProfileSerializer(coach).data)

    def patch(self, request):
        gym_id = request.query_params.get("gym_id") or request.data.get("gym_id")
        coach = ensure_coach(request.user, gym_id)
        ser = CoachProfileUpdateSerializer(coach, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(CoachProfileSerializer(coach).data)


class ExerciseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = ExerciseSerializer

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs["gym_id"])

    def get_queryset(self):
        coach = self.get_coach()
        qs = Exercise.objects.filter(Q(gym_id=coach.gym_id) | Q(gym__isnull=True, is_public=True))
        muscle = self.request.query_params.get("muscle_group")
        if muscle:
            qs = qs.filter(muscle_group=muscle)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def perform_create(self, serializer):
        coach = self.get_coach()
        serializer.save(coach=coach, gym=coach.gym)


class ExerciseDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = ExerciseSerializer

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs["gym_id"])
        return Exercise.objects.filter(Q(gym_id=coach.gym_id) | Q(coach=coach))


class WorkoutListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs["gym_id"])

    def get_queryset(self):
        coach = self.get_coach()
        qs = WorkoutSession.objects.filter(coach=coach).prefetch_related("sets", "sets__exercise")
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        if date_from:
            qs = qs.filter(performed_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(performed_at__date__lte=date_to)
        return qs

    def get_serializer_class(self):
        return WorkoutSessionWriteSerializer if self.request.method == "POST" else WorkoutSessionSerializer

    def perform_create(self, serializer):
        coach = self.get_coach()
        student = serializer.validated_data["student"]
        if student.coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        serializer.save(coach=coach, gym=coach.gym)


class WorkoutDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs["gym_id"])
        return WorkoutSession.objects.filter(coach=coach).prefetch_related("sets", "sets__exercise")

    def get_serializer_class(self):
        return WorkoutSessionWriteSerializer if self.request.method in ("PUT", "PATCH") else WorkoutSessionSerializer


class PRListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = PersonalRecordSerializer

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs["gym_id"])

    def get_queryset(self):
        coach = self.get_coach()
        qs = PersonalRecord.objects.filter(coach=coach).select_related("exercise", "student")
        student_id = self.request.query_params.get("student_id")
        exercise_id = self.request.query_params.get("exercise_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        if exercise_id:
            qs = qs.filter(exercise_id=exercise_id)
        return qs

    def perform_create(self, serializer):
        coach = self.get_coach()
        student = serializer.validated_data["student"]
        if student.coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        serializer.save(coach=coach, gym=coach.gym)


class PRDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = PersonalRecordSerializer

    def get_queryset(self):
        return PersonalRecord.objects.filter(
            coach=ensure_coach(self.request.user, self.kwargs["gym_id"])
        )


class ProgressPhotoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = ProgressPhotoSerializer

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs["gym_id"])

    def get_queryset(self):
        qs = ProgressPhoto.objects.filter(coach=self.get_coach())
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        coach = self.get_coach()
        student = serializer.validated_data["student"]
        if student.coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        serializer.save(coach=coach, gym=coach.gym)


class ProgressPhotoDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = ProgressPhotoSerializer

    def get_queryset(self):
        return ProgressPhoto.objects.filter(
            coach=ensure_coach(self.request.user, self.kwargs["gym_id"])
        )


class ProgressChartView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]

    def get(self, request, gym_id):
        coach = ensure_coach(request.user, gym_id)
        student_id = request.query_params.get("student_id")
        days = int(request.query_params.get("days", 90))
        since = timezone.now() - timedelta(days=days)
        sessions = WorkoutSession.objects.filter(coach=coach, performed_at__gte=since)
        if student_id:
            sessions = sessions.filter(student_id=student_id)
        volume_by_day = []
        for s in sessions.prefetch_related("sets"):
            vol = sum(float(st.weight_kg or 0) * (st.reps or 0) for st in s.sets.all())
            volume_by_day.append({
                "date": s.performed_at.date().isoformat(),
                "volume": round(vol, 2),
                "session_id": s.id,
            })
        prs = PersonalRecord.objects.filter(coach=coach, achieved_at__gte=since.date())
        if student_id:
            prs = prs.filter(student_id=student_id)
        pr_series = [
            {
                "date": p.achieved_at.isoformat(),
                "exercise_id": p.exercise_id,
                "exercise_name": p.exercise.name,
                "value": float(p.value),
                "unit": p.unit,
            }
            for p in prs.select_related("exercise")
        ]
        stats = StudentMonthlyStat.objects.filter(coach=coach)
        if student_id:
            stats = stats.filter(student_id=student_id)
        weight_series = [
            {
                "year": st.year,
                "month": st.month,
                "weight_kg": float(st.weight_kg) if st.weight_kg is not None else None,
                "body_fat_percent": float(st.body_fat_percent) if st.body_fat_percent is not None else None,
            }
            for st in stats.order_by("year", "month")
        ]
        return Response({
            "days": days,
            "workout_volume": volume_by_day,
            "personal_records": pr_series,
            "body_metrics": weight_series,
            "sessions_count": sessions.count(),
        })


class LeaderboardView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]

    def get(self, request, gym_id):
        coach = ensure_coach(request.user, gym_id)
        metric = request.query_params.get("metric", "workouts")
        exercise_id = request.query_params.get("exercise_id")
        limit = min(int(request.query_params.get("limit", 20)), 50)
        students = CoachStudent.objects.filter(coach=coach, is_active=True)
        if metric == "pr" and exercise_id:
            prs = (
                PersonalRecord.objects.filter(
                    coach=coach, exercise_id=exercise_id, student__in=students
                )
                .values("student_id", "student__full_name")
                .annotate(best=Max("value"))
                .order_by("-best")[:limit]
            )
            rows = [
                {
                    "rank": i + 1,
                    "student_id": r["student_id"],
                    "student_name": r["student__full_name"],
                    "value": float(r["best"]),
                    "metric": "pr",
                }
                for i, r in enumerate(prs)
            ]
        else:
            counts = (
                WorkoutSession.objects.filter(coach=coach, student__in=students)
                .values("student_id", "student__full_name")
                .annotate(total=Count("id"))
                .order_by("-total")[:limit]
            )
            rows = [
                {
                    "rank": i + 1,
                    "student_id": r["student_id"],
                    "student_name": r["student__full_name"],
                    "value": r["total"],
                    "metric": "workouts",
                }
                for i, r in enumerate(counts)
            ]
        return Response({"metric": metric, "leaderboard": rows})


class FeedListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs["gym_id"])

    def get_queryset(self):
        return CoachPost.objects.filter(coach=self.get_coach()).select_related("student")

    def get_serializer_class(self):
        return CoachPostCreateSerializer if self.request.method == "POST" else CoachPostSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = []
        for post in qs:
            item = CoachPostSerializer(post).data
            item["likes_count"] = post.likes.count()
            item["comments_count"] = post.comments.count()
            item["liked_by_me"] = post.likes.filter(user=request.user).exists()
            data.append(item)
        return Response(data)

    def perform_create(self, serializer):
        coach = self.get_coach()
        student = serializer.validated_data.get("student")
        if student and student.coach_id != coach.id:
            raise ValidationError({"student": "شاگرد متعلق به شما نیست."})
        serializer.save(coach=coach)


class FeedDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = CoachPostSerializer

    def get_queryset(self):
        return CoachPost.objects.filter(
            coach=ensure_coach(self.request.user, self.kwargs["gym_id"])
        )


class FeedLikeToggleView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]

    def post(self, request, gym_id, post_id):
        coach = ensure_coach(request.user, gym_id)
        post = CoachPost.objects.filter(coach=coach, pk=post_id).first()
        if not post:
            return Response({"detail": "یافت نشد."}, status=404)
        like, created = FeedLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False, "likes_count": post.likes.count()})
        return Response({"liked": True, "likes_count": post.likes.count()})


class FeedCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]
    serializer_class = FeedCommentSerializer

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs["gym_id"])
        return FeedComment.objects.filter(
            post_id=self.kwargs["post_id"], post__coach=coach
        ).select_related("user")

    def perform_create(self, serializer):
        coach = ensure_coach(self.request.user, self.kwargs["gym_id"])
        post = CoachPost.objects.filter(coach=coach, pk=self.kwargs["post_id"]).first()
        if not post:
            raise ValidationError({"post": "پست یافت نشد."})
        serializer.save(user=self.request.user, post=post)


class AnalyticsView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoachOnly]

    def get(self, request, gym_id):
        coach = ensure_coach(request.user, gym_id)
        now = timezone.localtime()
        year = int(request.query_params.get("year", now.year))
        month = int(request.query_params.get("month", now.month))
        students = CoachStudent.objects.filter(coach=coach)
        return Response({
            "year": year,
            "month": month,
            "total_students": students.count(),
            "active_students": students.filter(is_active=True).count(),
            "workouts": WorkoutSession.objects.filter(
                coach=coach, performed_at__year=year, performed_at__month=month
            ).count(),
            "prs": PersonalRecord.objects.filter(
                coach=coach, achieved_at__year=year, achieved_at__month=month
            ).count(),
            "posts": CoachPost.objects.filter(
                coach=coach, created_at__year=year, created_at__month=month
            ).count(),
        })
