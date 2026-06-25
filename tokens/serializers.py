from rest_framework import serializers
from django.utils import timezone
from .models import GymToken


class GymTokenSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()
    gym_name = serializers.CharField(source="gym.name", read_only=True)
    gym_address = serializers.CharField(source="gym.address", read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    user = serializers.CharField(source="subscription.user.__str__", read_only=True)

    class Meta:
        model = GymToken
        fields = [
            "id",
            "token_code",
            "user",
            "gym",
            "gym_name",
            "gym_address",
            "status",
            "is_valid",
            "issued_at",
            "valid_until",
            "used_at",
            "qr_code",
        ]
        read_only_fields = fields

    def get_qr_code(self, obj):
        # فقط برای توکن‌های فعال QR تولید میشه
        if obj.status == "active":
            return obj.generate_qr_base64()
        return None


class RequestGymTokenSerializer(serializers.Serializer):
    gym_id = serializers.IntegerField(help_text="آیدی باشگاه")

    def validate_gym_id(self, value):
        from gym.models import Gym
        if not Gym.objects.filter(id=value).exists():
            raise serializers.ValidationError("باشگاه مورد نظر یافت نشد.")
        return value

    def validate(self, attrs):
        from subscriptions.models import UserSubscription

        user = self.context["request"].user
        gym_id = attrs["gym_id"]

        # بررسی اشتراک فعال
        subscription = UserSubscription.objects.filter(
            user=user,
            status="active",
            end_date__gt=timezone.now(),
        ).first()

        if not subscription:
            raise serializers.ValidationError("اشتراک فعالی ندارید.")

        if subscription.tokens_remaining <= 0:
            raise serializers.ValidationError("توکن‌های اشتراک شما تمام شده است.")

        # بررسی دسترسی به این باشگاه
        if not subscription.plan.gyms.filter(id=gym_id).exists():
            raise serializers.ValidationError("این باشگاه در پلن شما وجود ندارد.")

        # بررسی توکن فعال برای همین باشگاه
        existing = GymToken.objects.filter(
            subscription=subscription,
            gym_id=gym_id,
            status="active",
            valid_until__gt=timezone.now(),
        ).exists()

        if existing:
            raise serializers.ValidationError(
                "شما یک توکن فعال برای این باشگاه دارید. ابتدا آن را استفاده کنید."
            )

        attrs["subscription"] = subscription
        return attrs


class ValidateGymTokenSerializer(serializers.Serializer):
    token_code = serializers.UUIDField(help_text="کد توکن")