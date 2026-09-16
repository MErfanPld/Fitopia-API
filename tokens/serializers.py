from rest_framework import serializers
from django.utils import timezone
from .models import GymToken


class GymTokenSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()
    gym_name = serializers.SerializerMethodField()
    gym_address = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    user = serializers.CharField(source="subscription.user.__str__", read_only=True)
    is_universal = serializers.SerializerMethodField()

    class Meta:
        model = GymToken
        fields = [
            "id",
            "token_code",
            "user",
            "gym",
            "gym_name",
            "gym_address",
            "is_universal",
            "status",
            "is_valid",
            "issued_at",
            "valid_until",
            "used_at",
            "qr_code",
        ]
        read_only_fields = fields

    def get_qr_code(self, obj):
        if obj.status == "active":
            return obj.generate_qr_base64()
        return None

    def get_gym_name(self, obj):
        return obj.gym.name if obj.gym_id else None

    def get_gym_address(self, obj):
        return obj.gym.address if obj.gym_id else None

    def get_is_universal(self, obj):
        return obj.gym_id is None


class RequestGymTokenSerializer(serializers.Serializer):
    gym_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="آیدی باشگاه؛ اگر ارسال نشود بلیت سراسری صادر می‌شود.",
    )

    def validate_gym_id(self, value):
        if value is None:
            return value
        from gym.models import Gym
        if not Gym.objects.filter(id=value).exists():
            raise serializers.ValidationError("باشگاه مورد نظر یافت نشد.")
        return value

    def validate(self, attrs):
        from subscriptions.models import UserSubscription

        user = self.context["request"].user
        gym_id = attrs.get("gym_id")

        subscription = UserSubscription.objects.filter(
            user=user,
            status="active",
            end_date__gt=timezone.now(),
        ).first()

        if not subscription:
            raise serializers.ValidationError("اشتراک فعالی ندارید.")

        if subscription.tokens_remaining <= 0:
            raise serializers.ValidationError("توکن‌های اشتراک شما تمام شده است.")

        if gym_id is not None:
            if not subscription.plan.gyms.filter(id=gym_id).exists():
                raise serializers.ValidationError("این باشگاه در پلن شما وجود ندارد.")
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
        else:
            if not subscription.plan.gyms.exists():
                raise serializers.ValidationError("پلن شما هیچ باشگاهی ندارد.")
            existing = GymToken.objects.filter(
                subscription=subscription,
                gym__isnull=True,
                status="active",
                valid_until__gt=timezone.now(),
            ).exists()
            if existing:
                raise serializers.ValidationError(
                    "شما یک بلیت سراسری فعال دارید. ابتدا آن را استفاده کنید."
                )

        attrs["subscription"] = subscription
        return attrs


class ValidateGymTokenSerializer(serializers.Serializer):
    token_code = serializers.UUIDField(help_text="کد توکن")
    gym_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="آیدی باشگاهی که اسکن در آن انجام می‌شود (برای بلیت سراسری الزامی است).",
    )
