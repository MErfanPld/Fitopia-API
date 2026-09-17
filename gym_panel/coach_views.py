from django.db.models import Avg
from django.utils import timezone

from rest_framework import generics, status, views
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from gym_panel.permissions import IsGymStaff
from .coach_permissions import IsCoach, ensure_coach
from .coach_models import (
    CoachStudent, CoachPost, TrainingProgram, DietProgram,
    SupplementProgram, StudentMonthlyStat,
)
from .coach_serializers import (
    CoachProfileSerializer, CoachProfileUpdateSerializer,
    CoachStudentSerializer, CoachStudentCreateSerializer,
    CoachPostSerializer, CoachPostCreateSerializer,
    TrainingProgramSerializer, TrainingProgramWriteSerializer,
    DietProgramSerializer, DietProgramWriteSerializer,
    SupplementProgramSerializer, SupplementProgramWriteSerializer,
    StudentMonthlyStatSerializer,
)


class CoachMeView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        gym_id = request.query_params.get("gym_id")
        coach = ensure_coach(request.user, gym_id)
        return Response(CoachProfileSerializer(coach).data)

    def patch(self, request):
        gym_id = request.query_params.get("gym_id") or request.data.get("gym_id")
        coach = ensure_coach(request.user, gym_id)
        ser = CoachProfileUpdateSerializer(coach, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(CoachProfileSerializer(coach).data)


class CoachStudentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs.get("gym_id"))

    def get_queryset(self):
        coach = self.get_coach()
        qs = CoachStudent.objects.filter(coach=coach)
        if self.request.query_params.get("active") == "1":
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CoachStudentCreateSerializer
        return CoachStudentSerializer

    def perform_create(self, serializer):
        coach = self.get_coach()
        serializer.save(coach=coach, gym=coach.gym)


class CoachStudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CoachStudentSerializer

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs.get("gym_id"))
        return CoachStudent.objects.filter(coach=coach)


class CoachPostListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs.get("gym_id"))

    def get_queryset(self):
        coach = self.get_coach()
        qs = CoachPost.objects.filter(coach=coach).select_related("student")
        ptype = self.request.query_params.get("post_type")
        if ptype in ("coach", "student", "general"):
            qs = qs.filter(post_type=ptype)
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CoachPostCreateSerializer
        return CoachPostSerializer

    def perform_create(self, serializer):
        coach = self.get_coach()
        student = serializer.validated_data.get("student")
        if student and student.coach_id != coach.id:
            raise ValidationError({"student": "این شاگرد متعلق به شما نیست."})
        serializer.save(coach=coach)


class CoachPostDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    serializer_class = CoachPostSerializer

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs.get("gym_id"))
        return CoachPost.objects.filter(coach=coach)


class TrainingProgramListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs.get("gym_id"))

    def get_queryset(self):
        coach = self.get_coach()
        qs = TrainingProgram.objects.filter(coach=coach).prefetch_related("exercises")
        for key in ("student_id", "year", "month"):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{key if key != "student_id" else "student_id": val})
        return qs

    def get_serializer_class(self):
        return TrainingProgramWriteSerializer if self.request.method == "POST" else TrainingProgramSerializer

    def perform_create(self, serializer):
        coach = self.get_coach()
        if serializer.validated_data["student"].coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        serializer.save(coach=coach)


class TrainingProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs.get("gym_id"))
        return TrainingProgram.objects.filter(coach=coach).prefetch_related("exercises")

    def get_serializer_class(self):
        return TrainingProgramWriteSerializer if self.request.method in ("PUT", "PATCH") else TrainingProgramSerializer


class DietProgramListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs.get("gym_id"))

    def get_queryset(self):
        coach = self.get_coach()
        qs = DietProgram.objects.filter(coach=coach).prefetch_related("meals")
        for key, field in (("student_id", "student_id"), ("year", "year"), ("month", "month")):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{field: val})
        return qs

    def get_serializer_class(self):
        return DietProgramWriteSerializer if self.request.method == "POST" else DietProgramSerializer

    def perform_create(self, serializer):
        coach = self.get_coach()
        if serializer.validated_data["student"].coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        serializer.save(coach=coach)


class DietProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs.get("gym_id"))
        return DietProgram.objects.filter(coach=coach).prefetch_related("meals")

    def get_serializer_class(self):
        return DietProgramWriteSerializer if self.request.method in ("PUT", "PATCH") else DietProgramSerializer


class SupplementProgramListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs.get("gym_id"))

    def get_queryset(self):
        coach = self.get_coach()
        qs = SupplementProgram.objects.filter(coach=coach).prefetch_related("items")
        for key, field in (("student_id", "student_id"), ("year", "year"), ("month", "month")):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{field: val})
        return qs

    def get_serializer_class(self):
        return SupplementProgramWriteSerializer if self.request.method == "POST" else SupplementProgramSerializer

    def perform_create(self, serializer):
        coach = self.get_coach()
        if serializer.validated_data["student"].coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        serializer.save(coach=coach)


class SupplementProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs.get("gym_id"))
        return SupplementProgram.objects.filter(coach=coach).prefetch_related("items")

    def get_serializer_class(self):
        return SupplementProgramWriteSerializer if self.request.method in ("PUT", "PATCH") else SupplementProgramSerializer


class StudentStatListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    serializer_class = StudentMonthlyStatSerializer

    def get_coach(self):
        return ensure_coach(self.request.user, self.kwargs.get("gym_id"))

    def get_queryset(self):
        coach = self.get_coach()
        qs = StudentMonthlyStat.objects.filter(coach=coach)
        for key, field in (("student_id", "student_id"), ("year", "year"), ("month", "month")):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{field: val})
        return qs

    def perform_create(self, serializer):
        coach = self.get_coach()
        student = serializer.validated_data["student"]
        if student.coach_id != coach.id:
            raise PermissionDenied("شاگرد متعلق به شما نیست.")
        year = serializer.validated_data["year"]
        month = serializer.validated_data["month"]
        defaults = {k: v for k, v in serializer.validated_data.items() if k not in ("student", "year", "month", "coach")}
        defaults["coach"] = coach
        obj, _ = StudentMonthlyStat.objects.update_or_create(
            student=student, year=year, month=month, defaults=defaults
        )
        serializer.instance = obj


class StudentStatDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]
    serializer_class = StudentMonthlyStatSerializer

    def get_queryset(self):
        coach = ensure_coach(self.request.user, self.kwargs.get("gym_id"))
        return StudentMonthlyStat.objects.filter(coach=coach)


class CoachMonthlyAnalyticsView(views.APIView):
    permission_classes = [IsAuthenticated, IsGymStaff, IsCoach]

    def get(self, request, gym_id):
        coach = ensure_coach(request.user, gym_id)
        now = timezone.localtime()
        year = int(request.query_params.get("year", now.year))
        month = int(request.query_params.get("month", now.month))
        students = CoachStudent.objects.filter(coach=coach)
        stats = StudentMonthlyStat.objects.filter(coach=coach, year=year, month=month)
        avg_adh = stats.aggregate(a=Avg("adherence_percent"))["a"]
        return Response({
            "year": year,
            "month": month,
            "total_students": students.count(),
            "active_students": students.filter(is_active=True).count(),
            "training_programs": TrainingProgram.objects.filter(coach=coach, year=year, month=month).count(),
            "diet_programs": DietProgram.objects.filter(coach=coach, year=year, month=month).count(),
            "supplement_programs": SupplementProgram.objects.filter(coach=coach, year=year, month=month).count(),
            "posts_count": CoachPost.objects.filter(coach=coach, created_at__year=year, created_at__month=month).count(),
            "avg_adherence": float(avg_adh) if avg_adh is not None else None,
            "stats": StudentMonthlyStatSerializer(stats, many=True).data,
        })
