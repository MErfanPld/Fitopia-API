from django.db import transaction
from django.db.models import Sum, Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema

from gym.models import Gym, Sport
from .models import (
    GymOffering, Course, CourseEnrollment, GymCustomer, SingleSessionPurchase,
    GymStaffAccess, StaffPermission, GymVisit, FinanceTransaction,
    CustomerPayment, Refund, AuditLog,
)
from .permissions import IsGymStaff, has_gym_access, user_has_perm, get_staff_access
from .management_serializers import (
    GymOfferingSerializer, CourseSerializer, CourseEnrollmentSerializer,
    GymCustomerExpandedSerializer, SingleSessionSerializer, StaffAccessSerializer,
    StaffPermissionAssignSerializer, CheckInSerializer, CheckOutSerializer,
    GymVisitSerializer, FinanceTransactionSerializer, CustomerPaymentSerializer,
    RefundSerializer, AuditLogSerializer,
)


def _gym_or_403(user, gym_id):
    if not has_gym_access(user, gym_id):
        raise PermissionDenied("شما به این باشگاه دسترسی ندارید.")
    return get_object_or_404(Gym, id=gym_id)


def _require_perm(user, gym_id, code):
    if not user_has_perm(user, gym_id, code):
        raise PermissionDenied("مجوز کافی ندارید.")


def _audit(user, gym, action, obj=None, metadata=None):
    AuditLog.objects.create(
        gym=gym,
        user=user,
        action=action,
        object_type=obj.__class__.__name__ if obj else "",
        object_id=str(getattr(obj, "pk", "")) if obj else "",
        metadata=metadata or {},
    )


@extend_schema(tags=["gym-mgmt-offerings"])
class OfferingListCreateView(generics.ListCreateAPIView):
    serializer_class = GymOfferingSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return GymOffering.objects.filter(gym_id=gym_id).select_related(
            "sport"
        ).prefetch_related("schedules", "coaches")

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "offering.manage")
        offering = serializer.save(gym=gym)
        gym.sports.add(offering.sport)
        _audit(self.request.user, gym, "offering.create", offering)


@extend_schema(tags=["gym-mgmt-offerings"])
class OfferingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GymOfferingSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return GymOffering.objects.filter(gym_id=gym_id).prefetch_related(
            "schedules", "coaches"
        )

    def perform_update(self, serializer):
        _require_perm(self.request.user, self.kwargs["gym_id"], "offering.manage")
        offering = serializer.save()
        _audit(self.request.user, offering.gym, "offering.update", offering)

    def perform_destroy(self, instance):
        _require_perm(self.request.user, self.kwargs["gym_id"], "offering.manage")
        _audit(self.request.user, instance.gym, "offering.delete", instance)
        instance.delete()


@extend_schema(tags=["gym-mgmt-courses"])
class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return Course.objects.filter(gym_id=gym_id).select_related(
            "sport", "coach", "offering"
        )

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "course.create")
        course = serializer.save(gym=gym)
        _audit(self.request.user, gym, "course.create", course)


@extend_schema(tags=["gym-mgmt-courses"])
class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return Course.objects.filter(gym_id=gym_id)

    def perform_update(self, serializer):
        _require_perm(self.request.user, self.kwargs["gym_id"], "course.update")
        course = serializer.save()
        _audit(self.request.user, course.gym, "course.update", course)

    def perform_destroy(self, instance):
        _require_perm(self.request.user, self.kwargs["gym_id"], "course.update")
        _audit(self.request.user, instance.gym, "course.delete", instance)
        instance.delete()


@extend_schema(tags=["gym-mgmt-courses"])
class CourseEnrollView(views.APIView):
    permission_classes = [IsGymStaff]

    def post(self, request, gym_id, course_id):
        gym = _gym_or_403(request.user, gym_id)
        _require_perm(request.user, gym_id, "course.enroll")
        course = get_object_or_404(Course, id=course_id, gym_id=gym_id)
        customer_id = request.data.get("customer")
        if not customer_id:
            raise ValidationError({"customer": "الزامی است."})
        customer = get_object_or_404(GymCustomer, id=customer_id)
        if customer.gym_id != gym.id:
            raise ValidationError("مشتری متعلق به این باشگاه نیست.")
        if course.remaining_capacity <= 0:
            raise ValidationError("ظرفیت دوره تکمیل است.")
        if CourseEnrollment.objects.filter(
            course=course, customer=customer, status="active"
        ).exists():
            raise ValidationError("این مشتری قبلاً در دوره ثبت‌نام شده است.")
        price_paid = request.data.get("price_paid", course.price)
        try:
            price_paid = int(price_paid)
        except (TypeError, ValueError):
            price_paid = course.price
        enrollment = CourseEnrollment.objects.create(
            course=course,
            customer=customer,
            price_paid=price_paid,
            status="active",
        )
        if course.remaining_capacity <= 0:
            course.status = "full"
            course.save(update_fields=["status"])
        _audit(request.user, gym, "course.enroll", enrollment)
        return Response(
            CourseEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["gym-mgmt-customers"])
class CustomerExpandedListCreateView(generics.ListCreateAPIView):
    serializer_class = GymCustomerExpandedSerializer
    permission_classes = [IsGymStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        _require_perm(self.request.user, gym_id, "customer.view")
        qs = GymCustomer.objects.filter(gym_id=gym_id).select_related(
            "sport", "coach", "added_by"
        )
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) | Q(phone__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "customer.create")
        customer = serializer.save(
            gym=gym,
            source="manual",
            added_by=self.request.user,
            sessions_remaining=serializer.validated_data.get("sessions_total"),
        )
        _audit(self.request.user, gym, "customer.create", customer)


@extend_schema(tags=["gym-mgmt-customers"])
class CustomerExpandedDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GymCustomerExpandedSerializer
    permission_classes = [IsGymStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return GymCustomer.objects.filter(gym_id=gym_id)

    def retrieve(self, request, *args, **kwargs):
        _require_perm(request.user, self.kwargs["gym_id"], "customer.view")
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        _require_perm(self.request.user, self.kwargs["gym_id"], "customer.update")
        customer = serializer.save()
        _audit(self.request.user, customer.gym, "customer.update", customer)

    def perform_destroy(self, instance):
        _require_perm(self.request.user, self.kwargs["gym_id"], "customer.delete")
        _audit(self.request.user, instance.gym, "customer.delete", instance, {
            "full_name": instance.full_name,
        })
        instance.delete()


@extend_schema(tags=["gym-mgmt-sessions"])
class SingleSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = SingleSessionSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return SingleSessionPurchase.objects.filter(gym_id=gym_id).select_related(
            "customer", "sport"
        )

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "finance.create")
        customer = serializer.validated_data["customer"]
        if customer.gym_id != gym.id:
            raise ValidationError("مشتری متعلق به این باشگاه نیست.")
        with transaction.atomic():
            session = serializer.save(gym=gym)
            tx = FinanceTransaction.objects.create(
                gym=gym,
                type="income",
                category="single_session",
                amount=session.price,
                date=timezone.now().date(),
                description=f"جلسه تکی — {customer.full_name}",
                customer=customer,
                created_by=self.request.user,
                status="completed",
            )
            session.transaction = tx
            session.save(update_fields=["transaction"])
            _audit(self.request.user, gym, "single_session.create", session)
