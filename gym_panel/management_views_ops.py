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


@extend_schema(tags=["gym-mgmt-employees"])
class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = StaffAccessSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        _require_perm(self.request.user, gym_id, "employee.view")
        return GymStaffAccess.objects.filter(gym_id=gym_id).select_related("user")

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "employee.manage")
        access = serializer.save(gym=gym)
        user = access.user
        if not user.is_staff_user:
            user.is_staff_user = True
            user.save(update_fields=["is_staff_user"])
        _audit(self.request.user, gym, "employee.create", access)


@extend_schema(tags=["gym-mgmt-employees"])
class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StaffAccessSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        return GymStaffAccess.objects.filter(gym_id=gym_id)

    def perform_update(self, serializer):
        _require_perm(self.request.user, self.kwargs["gym_id"], "employee.manage")
        access = serializer.save()
        _audit(self.request.user, access.gym, "employee.update", access)

    def perform_destroy(self, instance):
        _require_perm(self.request.user, self.kwargs["gym_id"], "employee.manage")
        _audit(self.request.user, instance.gym, "employee.delete", instance)
        instance.delete()


@extend_schema(tags=["gym-mgmt-employees"])
class EmployeePermissionsView(views.APIView):
    permission_classes = [IsGymStaff]

    def put(self, request, gym_id, pk):
        gym = _gym_or_403(request.user, gym_id)
        _require_perm(request.user, gym_id, "employee.manage")
        access = get_object_or_404(GymStaffAccess, id=pk, gym_id=gym_id)
        ser = StaffPermissionAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        valid_codes = {c[0] for c in StaffPermission.CODE_CHOICES}
        codes = [c for c in ser.validated_data["codes"] if c in valid_codes]
        access.permissions.all().delete()
        StaffPermission.objects.bulk_create([
            StaffPermission(staff_access=access, code=c) for c in codes
        ])
        _audit(request.user, gym, "employee.permissions", access, {"codes": codes})
        return Response({"codes": codes})


@extend_schema(tags=["gym-mgmt-attendance"])
class CheckInView(views.APIView):
    permission_classes = [IsGymStaff]

    def post(self, request, gym_id):
        gym = _gym_or_403(request.user, gym_id)
        _require_perm(request.user, gym_id, "attendance.create")
        ser = CheckInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        customer = get_object_or_404(
            GymCustomer, id=ser.validated_data["customer_id"], gym_id=gym_id
        )
        if GymVisit.objects.filter(customer=customer, is_open=True).exists():
            raise ValidationError("این مشتری هم‌اکنون داخل باشگاه است.")
        now = timezone.now()
        visit = GymVisit.objects.create(
            gym=gym,
            customer=customer,
            sport_id=ser.validated_data.get("sport_id"),
            price=0,
            source=ser.validated_data["method"],
            method=ser.validated_data["method"],
            check_in_at=now,
            is_open=True,
            registered_by=request.user,
            guest_name=customer.full_name,
            guest_phone=customer.phone or "",
        )
        customer.last_visit_at = now
        customer.sessions_used = (customer.sessions_used or 0) + 1
        if customer.sessions_remaining is not None and customer.sessions_remaining > 0:
            customer.sessions_remaining -= 1
        customer.save(update_fields=[
            "last_visit_at", "sessions_used", "sessions_remaining", "updated_at"
        ])
        _audit(request.user, gym, "attendance.check_in", visit)
        return Response(GymVisitSerializer(visit).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["gym-mgmt-attendance"])
class CheckOutView(views.APIView):
    permission_classes = [IsGymStaff]

    def post(self, request, gym_id):
        gym = _gym_or_403(request.user, gym_id)
        _require_perm(request.user, gym_id, "attendance.create")
        ser = CheckOutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        visit = get_object_or_404(
            GymVisit, id=ser.validated_data["visit_id"], gym_id=gym_id
        )
        if not visit.is_open:
            raise ValidationError("این حضور قبلاً بسته شده یا ورود ثبت نشده است.")
        visit.check_out_at = timezone.now()
        visit.is_open = False
        visit.save(update_fields=["check_out_at", "is_open"])
        _audit(request.user, gym, "attendance.check_out", visit)
        return Response(GymVisitSerializer(visit).data)


@extend_schema(tags=["gym-mgmt-attendance"])
class AttendanceListView(generics.ListAPIView):
    serializer_class = GymVisitSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        _require_perm(self.request.user, gym_id, "attendance.view")
        qs = GymVisit.objects.filter(gym_id=gym_id).select_related("customer", "sport")
        if self.request.query_params.get("open") == "1":
            qs = qs.filter(is_open=True)
        if self.request.query_params.get("today") == "1":
            today = timezone.now().date()
            qs = qs.filter(created_at__date=today)
        customer_id = self.request.query_params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs


@extend_schema(tags=["gym-mgmt-attendance"])
class AttendanceStatsView(views.APIView):
    permission_classes = [IsGymStaff]

    def get(self, request, gym_id):
        _gym_or_403(request.user, gym_id)
        _require_perm(request.user, gym_id, "attendance.view")
        today = timezone.now().date()
        month_start = today.replace(day=1)
        base = GymVisit.objects.filter(gym_id=gym_id)
        return Response({
            "today_visits": base.filter(created_at__date=today).count(),
            "currently_inside": base.filter(is_open=True).count(),
            "month_visits": base.filter(created_at__date__gte=month_start).count(),
            "total_visits": base.count(),
        })


@extend_schema(tags=["gym-mgmt-finance"])
class FinanceTransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = FinanceTransactionSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        _require_perm(self.request.user, gym_id, "finance.view")
        qs = FinanceTransaction.objects.filter(gym_id=gym_id)
        t = self.request.query_params.get("type")
        if t in ("income", "expense"):
            qs = qs.filter(type=t)
        return qs

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "finance.create")
        tx = serializer.save(gym=gym, created_by=self.request.user)
        _audit(self.request.user, gym, "finance.create", tx)


@extend_schema(tags=["gym-mgmt-finance"])
class CustomerPaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerPaymentSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        _require_perm(self.request.user, gym_id, "finance.view")
        return CustomerPayment.objects.filter(gym_id=gym_id).select_related("customer")

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "finance.create")
        customer = serializer.validated_data["customer"]
        if customer.gym_id != gym.id:
            raise ValidationError("مشتری متعلق به این باشگاه نیست.")
        with transaction.atomic():
            payment = serializer.save(gym=gym, created_by=self.request.user)
            if payment.amount_paid > 0:
                tx = FinanceTransaction.objects.create(
                    gym=gym,
                    type="income",
                    category="membership",
                    amount=payment.amount_paid,
                    date=timezone.now().date(),
                    description=payment.description or f"پرداخت مشتری {customer.full_name}",
                    payment_method=payment.payment_method,
                    reference_number=payment.reference_number,
                    customer=customer,
                    course=payment.related_course,
                    created_by=self.request.user,
                    status="completed",
                )
                payment.related_transaction = tx
                payment.save(update_fields=["related_transaction"])
            _audit(self.request.user, gym, "payment.create", payment)


@extend_schema(tags=["gym-mgmt-finance"])
class RefundCreateView(generics.CreateAPIView):
    serializer_class = RefundSerializer
    permission_classes = [IsGymStaff]

    def perform_create(self, serializer):
        gym = _gym_or_403(self.request.user, self.kwargs["gym_id"])
        _require_perm(self.request.user, gym.id, "finance.refund")
        tx = serializer.validated_data["original_transaction"]
        if tx.gym_id != gym.id:
            raise ValidationError("تراکنش متعلق به این باشگاه نیست.")
        refund = serializer.save(
            gym=gym, operator=self.request.user, status="completed",
            completed_at=timezone.now(),
        )
        total_refunded = Refund.objects.filter(
            original_transaction=tx, status="completed"
        ).aggregate(s=Sum("amount"))["s"] or 0
        if total_refunded >= tx.amount:
            tx.status = "refunded"
            tx.save(update_fields=["status"])
        _audit(self.request.user, gym, "refund.create", refund)


@extend_schema(tags=["gym-mgmt-finance"])
class FinanceReportView(views.APIView):
    permission_classes = [IsGymStaff]

    def get(self, request, gym_id):
        _gym_or_403(request.user, gym_id)
        _require_perm(request.user, gym_id, "finance.report")
        today = timezone.now().date()
        month_start = today.replace(day=1)
        base = FinanceTransaction.objects.filter(
            gym_id=gym_id, status="completed"
        )

        def agg(qs):
            income = qs.filter(type="income").aggregate(s=Sum("amount"))["s"] or 0
            expense = qs.filter(type="expense").aggregate(s=Sum("amount"))["s"] or 0
            return {"income": income, "expense": expense, "net": income - expense}

        by_category = list(
            base.filter(type="income").values("category").annotate(
                total=Sum("amount")
            ).order_by("-total")
        )
        debts = []
        for p in CustomerPayment.objects.filter(gym_id=gym_id).select_related("customer"):
            bal = p.remaining_balance
            if bal > 0:
                debts.append({
                    "customer_id": p.customer_id,
                    "customer_name": p.customer.full_name,
                    "remaining": bal,
                    "payment_id": p.id,
                })

        return Response({
            "daily": agg(base.filter(date=today)),
            "monthly": agg(base.filter(date__gte=month_start)),
            "income_by_category": by_category,
            "outstanding_balances": debts,
        })


@extend_schema(tags=["gym-mgmt-audit"])
class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsGymStaff]

    def get_queryset(self):
        gym_id = self.kwargs["gym_id"]
        _gym_or_403(self.request.user, gym_id)
        access = get_staff_access(self.request.user, gym_id)
        if not access or access.role not in ("owner", "manager"):
            raise PermissionDenied("فقط مالک/مدیر به لاگ دسترسی دارند.")
        return AuditLog.objects.filter(gym_id=gym_id)[:200]
