from rest_framework import serializers
from django.utils import timezone
from .models import (
    GymOffering, GymOfferingSchedule, Course, CourseEnrollment,
    SingleSessionPurchase, StaffPermission, GymStaffAccess,
    FinanceTransaction, CustomerPayment, Refund, AuditLog,
    GymCustomer, GymVisit,
)


class GymOfferingScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymOfferingSchedule
        fields = ["id", "day_of_week", "start_time", "end_time"]

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        if start and end and end <= start:
            raise serializers.ValidationError("ساعت پایان باید بعد از شروع باشد.")
        return attrs


class GymOfferingSerializer(serializers.ModelSerializer):
    schedules = GymOfferingScheduleSerializer(many=True, required=False)
    sport_name = serializers.CharField(source="sport.name", read_only=True)

    class Meta:
        model = GymOffering
        fields = [
            "id", "gym", "sport", "sport_name", "description", "coaches",
            "capacity", "single_session_price", "course_price", "monthly_price",
            "duration_minutes", "skill_level", "gender_restriction",
            "min_age", "max_age", "is_active", "schedules",
            "created_at", "updated_at",
        ]
        read_only_fields = ["gym", "created_at", "updated_at"]

    def create(self, validated_data):
        schedules = validated_data.pop("schedules", [])
        coaches = validated_data.pop("coaches", [])
        offering = GymOffering.objects.create(**validated_data)
        if coaches:
            offering.coaches.set(coaches)
        for s in schedules:
            GymOfferingSchedule.objects.create(offering=offering, **s)
        return offering

    def update(self, instance, validated_data):
        schedules = validated_data.pop("schedules", None)
        coaches = validated_data.pop("coaches", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if coaches is not None:
            instance.coaches.set(coaches)
        if schedules is not None:
            instance.schedules.all().delete()
            for s in schedules:
                GymOfferingSchedule.objects.create(offering=instance, **s)
        return instance


class CourseSerializer(serializers.ModelSerializer):
    enrollment_count = serializers.IntegerField(read_only=True)
    remaining_capacity = serializers.IntegerField(read_only=True)
    sport_name = serializers.CharField(source="sport.name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "gym", "sport", "sport_name", "offering", "coach", "title",
            "description", "start_date", "end_date", "start_time", "end_time",
            "days_of_week", "capacity", "price", "status", "is_active",
            "enrollment_count", "remaining_capacity", "created_at", "updated_at",
        ]
        read_only_fields = ["gym", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start and end and end < start:
            raise serializers.ValidationError("تاریخ پایان نمی‌تواند قبل از شروع باشد.")
        return attrs


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            "id", "course", "customer", "customer_name", "status",
            "enrolled_at", "price_paid",
        ]
        read_only_fields = ["enrolled_at"]


class GymCustomerExpandedSerializer(serializers.ModelSerializer):
    sessions_remaining_calc = serializers.SerializerMethodField()

    class Meta:
        model = GymCustomer
        fields = [
            "id", "gym", "fitopia_user", "full_name", "phone", "sport", "coach",
            "source", "added_by", "sessions_total", "sessions_remaining",
            "sessions_used", "price_paid", "join_date", "photo",
            "membership_status", "membership_type", "membership_start",
            "membership_end", "notes", "is_active", "last_visit_at",
            "sessions_remaining_calc", "created_at", "updated_at",
        ]
        read_only_fields = ["gym", "added_by", "created_at", "updated_at", "last_visit_at"]

    def get_sessions_remaining_calc(self, obj):
        if obj.sessions_total is None:
            return obj.sessions_remaining
        return max(0, (obj.sessions_total or 0) - (obj.sessions_used or 0))


class SingleSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleSessionPurchase
        fields = [
            "id", "gym", "customer", "sport", "price", "status",
            "purchased_at", "used_at", "expires_at", "transaction",
        ]
        read_only_fields = ["gym", "purchased_at", "used_at", "transaction"]


class StaffAccessSerializer(serializers.ModelSerializer):
    permission_codes = serializers.SerializerMethodField()
    user_phone = serializers.CharField(source="user.phone_number", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GymStaffAccess
        fields = [
            "id", "user", "username", "user_phone", "gym", "role", "is_active",
            "start_date", "end_date", "employee_number", "permission_codes", "created_at",
        ]
        read_only_fields = ["gym", "created_at"]

    def get_permission_codes(self, obj):
        return list(obj.permissions.values_list("code", flat=True))


class StaffPermissionAssignSerializer(serializers.Serializer):
    codes = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class CheckInSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    method = serializers.ChoiceField(
        choices=["qr", "token", "manual", "membership"], default="manual"
    )
    sport_id = serializers.IntegerField(required=False, allow_null=True)


class CheckOutSerializer(serializers.Serializer):
    visit_id = serializers.IntegerField()


class GymVisitSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = GymVisit
        fields = [
            "id", "gym", "customer", "customer_name", "sport", "price", "source",
            "method", "check_in_at", "check_out_at", "is_open",
            "registered_by", "guest_name", "guest_phone", "created_at",
        ]
        read_only_fields = fields


class FinanceTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceTransaction
        fields = [
            "id", "gym", "type", "category", "amount", "date", "description",
            "payment_method", "reference_number", "customer", "employee",
            "course", "created_by", "status", "created_at",
        ]
        read_only_fields = ["gym", "created_by", "created_at"]


class CustomerPaymentSerializer(serializers.ModelSerializer):
    remaining_balance = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomerPayment
        fields = [
            "id", "gym", "customer", "total_price", "amount_paid", "discount",
            "remaining_balance", "description", "payment_method",
            "reference_number", "related_course", "related_transaction",
            "created_by", "created_at",
        ]
        read_only_fields = ["gym", "created_by", "created_at"]

    def validate(self, attrs):
        total = attrs.get("total_price", getattr(self.instance, "total_price", 0))
        paid = attrs.get("amount_paid", getattr(self.instance, "amount_paid", 0))
        discount = attrs.get("discount", getattr(self.instance, "discount", 0))
        if paid < 0 or discount < 0 or total < 0:
            raise serializers.ValidationError("مبالغ نمی‌توانند منفی باشند.")
        if paid > max(0, total - discount):
            raise serializers.ValidationError(
                "مبلغ پرداختی نمی‌تواند از مبلغ قابل پرداخت بیشتر باشد."
            )
        return attrs


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "id", "gym", "original_transaction", "amount", "reason",
            "status", "operator", "created_at", "completed_at",
        ]
        read_only_fields = ["gym", "operator", "created_at", "completed_at", "status"]

    def validate(self, attrs):
        tx = attrs.get("original_transaction")
        amount = attrs.get("amount")
        if tx and amount is not None:
            if amount > tx.amount:
                raise serializers.ValidationError(
                    "مبلغ استرداد نمی‌تواند از مبلغ تراکنش بیشتر باشد."
                )
            if tx.type != "income":
                raise serializers.ValidationError("فقط تراکنش درآمد قابل استرداد است.")
        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id", "gym", "user", "action", "object_type", "object_id",
            "metadata", "created_at",
        ]
        read_only_fields = fields
