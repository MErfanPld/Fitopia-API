from rest_framework import serializers
from .models import *
from gym.models import Gym, GymCoach, GymPrice, Sport


class GymCoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymCoach
        fields = ["id", "full_name", "image", "specialty", "sports"]

class GymPanelLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class GymStaffAccessSerializer(serializers.ModelSerializer):
    gym_name = serializers.CharField(source="gym.name", read_only=True)

    class Meta:
        model = GymStaffAccess
        fields = ["id", "gym", "gym_name", "role"]
        

# فیلدهای آزاد
class GymPanelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = [
            "description", "phone", "whatsapp", "telegram",
            "instagram", "website", "cover_image", "rules", "working_hours",
        ]
        extra_kwargs = {f: {"required": False} for f in fields}


# ثبت تیکت برای فیلدهای محدود (name/address/lat/long)
class FieldEditRequestSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("حداقل یک فیلد باید ارسال شود.")
        allowed = {"name", "address", "latitude", "longitude"}
        if not set(attrs.keys()) <= allowed:
            raise serializers.ValidationError("فیلد غیرمجاز ارسال شده.")
        return attrs


# پیشنهاد رشته‌ی کاملاً جدید
class SuggestNewSportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    category_id = serializers.IntegerField()

    def validate_category_id(self, value):
        from gym.models import SportCategory
        if not SportCategory.objects.filter(id=value).exists():
            raise serializers.ValidationError("دسته‌بندی یافت نشد.")
        return value


from .models import GymChangeRequest, GymTicketMessage


class GymTicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymTicketMessage
        fields = ["id", "sender_role", "message", "created_at"]
        read_only_fields = ["id", "sender_role", "created_at"]


class GymTicketMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField()


class GymChangeRequestSerializer(serializers.ModelSerializer):
    messages = GymTicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = GymChangeRequest
        fields = [
            "id", "request_type", "payload", "status",
            "admin_note", "created_at", "reviewed_at", "messages",
        ]

# مدیریت رشته‌های موجود (GymPrice) — آزاد
class GymPriceSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source="sport.name", read_only=True)

    class Meta:
        model = GymPrice
        fields = ["id", "sport", "sport_name", "session_price", "monthly_price", "quarterly_price", "yearly_price"]

    def validate_sport(self, value):
        return value  # باید از لیست Sportهای موجود باشه؛ ModelSerializer خودش چک می‌کنه وجود داره یا نه
    

from .models import GymCustomer


class GymCustomerSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source="sport.name", read_only=True)
    is_fitopia_user = serializers.SerializerMethodField()

    class Meta:
        model = GymCustomer
        fields = [
            "id", "full_name", "phone", "sport", "sport_name",
            "join_date", "is_fitopia_user", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_is_fitopia_user(self, obj):
        return obj.fitopia_user_id is not None