from rest_framework import serializers
from django.db import transaction

from .models import *
from gym.models import Gym, GymCoach, GymPrice, Sport
from users.models import User


class GymCoachSerializer(serializers.ModelSerializer):
    """
    ساخت/ویرایش مربی توسط باشگاه‌دار.
    با ارسال username + password + phone_number حساب لاگین پنل مربی ساخته می‌شود.
    """
    username = serializers.CharField(required=False, allow_blank=True, write_only=True)
    password = serializers.CharField(
        required=False, write_only=True, min_length=6, style={"input_type": "password"}
    )
    phone_number = serializers.CharField(required=False, allow_blank=True, write_only=True)

    user_id = serializers.IntegerField(source="user.id", read_only=True, allow_null=True)
    login_username = serializers.CharField(source="user.username", read_only=True, allow_null=True)
    login_phone = serializers.CharField(source="user.phone_number", read_only=True, allow_null=True)
    has_login = serializers.SerializerMethodField()

    class Meta:
        model = GymCoach
        fields = [
            "id",
            "full_name",
            "image",
            "specialty",
            "bio",
            "sports",
            "is_active",
            "user_id",
            "login_username",
            "login_phone",
            "has_login",
            "username",
            "password",
            "phone_number",
        ]
        extra_kwargs = {
            "specialty": {"required": False, "allow_blank": True},
            "bio": {"required": False, "allow_blank": True},
        }

    def get_has_login(self, obj):
        return bool(obj.user_id)

    def validate(self, attrs):
        username = (attrs.get("username") or "").strip()
        password = attrs.get("password")
        phone = (attrs.get("phone_number") or "").strip()
        creating = self.instance is None

        wants_account = bool(username or phone or password)
        if wants_account:
            if not username:
                raise serializers.ValidationError({"username": "برای ساخت حساب، نام کاربری الزامی است."})
            if creating and not password:
                raise serializers.ValidationError({"password": "برای ساخت حساب، رمز عبور الزامی است."})
            if not phone:
                raise serializers.ValidationError({"phone_number": "برای ساخت حساب، شماره موبایل الزامی است."})

            qs_user = User.objects.filter(username=username)
            if self.instance and self.instance.user_id:
                qs_user = qs_user.exclude(pk=self.instance.user_id)
            if qs_user.exists():
                raise serializers.ValidationError({"username": "این نام کاربری قبلاً ثبت شده است."})

            qs_phone = User.objects.filter(phone_number=phone)
            if self.instance and self.instance.user_id:
                qs_phone = qs_phone.exclude(pk=self.instance.user_id)
            if qs_phone.exists():
                raise serializers.ValidationError({"phone_number": "این شماره موبایل قبلاً ثبت شده است."})

        attrs["username"] = username or None
        attrs["phone_number"] = phone or None
        return attrs

    def _ensure_staff_access(self, user, gym):
        access, created = GymStaffAccess.objects.get_or_create(
            user=user,
            gym=gym,
            defaults={"role": "coach", "is_active": True},
        )
        if not created:
            if access.role != "coach":
                # مالک/مدیر را عوض نکن؛ فقط اگر نقش عمومی staff بود به coach ببر
                if access.role in ("staff", "receptionist", ""):
                    access.role = "coach"
            access.is_active = True
            access.save(update_fields=["role", "is_active"])
        return access

    def _create_or_update_user(self, validated_data, gym, existing_user=None):
        username = validated_data.pop("username", None)
        password = validated_data.pop("password", None)
        phone_number = validated_data.pop("phone_number", None)

        if not username and not phone_number and not password:
            return existing_user

        if existing_user:
            user = existing_user
            if username:
                user.username = username
            if phone_number:
                user.phone_number = phone_number
            if password:
                user.set_password(password)
            user.is_staff_user = True
            user.is_active = True
            if validated_data.get("full_name") and not user.full_name:
                user.full_name = validated_data["full_name"]
            user.save()
        else:
            if not (username and password and phone_number):
                return None
            user = User.objects.create_user(
                username=username,
                phone_number=phone_number,
                password=password,
                full_name=validated_data.get("full_name") or username,
                is_staff_user=True,
                is_active=True,
            )
        self._ensure_staff_access(user, gym)
        return user

    @transaction.atomic
    def create(self, validated_data):
        sports = validated_data.pop("sports", [])
        gym = validated_data.pop("gym")
        user = self._create_or_update_user(validated_data, gym, existing_user=None)
        coach = GymCoach.objects.create(gym=gym, user=user, **validated_data)
        if sports:
            coach.sports.set(sports)
        return coach

    @transaction.atomic
    def update(self, instance, validated_data):
        sports = validated_data.pop("sports", None)
        gym = instance.gym
        user = self._create_or_update_user(
            validated_data, gym, existing_user=instance.user
        )
        if user is not None:
            instance.user = user
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if sports is not None:
            instance.sports.set(sports)
        return instance


class GymPanelLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class GymStaffAccessSerializer(serializers.ModelSerializer):
    gym_name = serializers.CharField(source="gym.name", read_only=True)

    class Meta:
        model = GymStaffAccess
        fields = ["id", "gym", "gym_name", "role"]


class GymPanelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = [
            "description", "phone", "whatsapp", "telegram",
            "instagram", "website", "cover_image", "rules", "working_hours",
        ]
        extra_kwargs = {f: {"required": False} for f in fields}


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


class GymPriceSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source="sport.name", read_only=True)

    class Meta:
        model = GymPrice
        fields = ["id", "sport", "sport_name", "session_price", "monthly_price", "quarterly_price", "yearly_price"]

    def validate_sport(self, value):
        return value


from .models import GymCustomer


class GymCustomerSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source="sport.name", read_only=True)
    is_fitopia_user = serializers.SerializerMethodField()
    added_by_name = serializers.CharField(source="added_by.full_name", read_only=True)

    class Meta:
        model = GymCustomer
        fields = [
            "id", "full_name", "phone", "sport", "sport_name",
            "source", "added_by", "added_by_name",
            "sessions_total", "sessions_remaining", "price_paid",
            "join_date", "is_fitopia_user", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "source", "added_by", "is_fitopia_user",
            "created_at", "updated_at",
        ]

    def get_is_fitopia_user(self, obj):
        return obj.fitopia_user_id is not None
