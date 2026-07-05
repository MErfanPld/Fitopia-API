from rest_framework import serializers
from django.utils import timezone
from .models import Plan, UserSubscription, UserDiscountProfile
from gym.models import Gym

class PlanSerializer(serializers.ModelSerializer):
    gyms_count = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "description",
            "price",
            "duration_days",
            "token_count",
            "gyms_count",
            "is_active",
            "order",
        ]

    def get_gyms_count(self, obj):
        return obj.gyms.count()


class PlanDetailSerializer(serializers.ModelSerializer):
    gyms = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "description",
            "price",
            "duration_days",
            "token_count",
            "gyms",
            "is_active",
        ]

    def get_gyms(self, obj):
        return obj.gyms.values("id", "name", "address", "cover_image")


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    tokens_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            "id",
            "plan",
            "plan_name",
            "status",
            "start_date",
            "end_date",
            "tokens_total",
            "tokens_used",
            "tokens_remaining",
            "is_active",
            "days_remaining",
            "paid_amount",
            "discount_applied",
            "created_at",
        ]
        read_only_fields = [
            "status",
            "start_date",
            "end_date",
            "tokens_total",
            "tokens_used",
            "paid_amount",
            "discount_applied",
            "created_at",
        ]

    def get_days_remaining(self, obj):
        if obj.end_date > timezone.now():
            return (obj.end_date - timezone.now()).days
        return 0


class PurchaseSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    use_discount = serializers.BooleanField(default=False)

    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError("پلن مورد نظر یافت نشد یا غیرفعال است.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        # بررسی اشتراک فعال
        active = UserSubscription.objects.filter(
            user=user,
            status="active",
            end_date__gt=timezone.now()
        ).exists()
        if active:
            raise serializers.ValidationError(
                "شما در حال حاضر یک اشتراک فعال دارید."
            )
        return attrs


class UserDiscountProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDiscountProfile
        fields = [
            "accumulated_leftover_tokens",
            "discount_amount",
            "is_used",
            "updated_at",
        ]
        
        
class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ["id", "name", "address", "phone"]


class SubscriptionGymsSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField(source="id")
    plan_name = serializers.CharField(source="plan.name")
    status = serializers.CharField()
    is_active = serializers.BooleanField()
    gyms = serializers.SerializerMethodField()

    def get_gyms(self, obj):
        return GymSerializer(obj.plan.gyms.all(), many=True).data