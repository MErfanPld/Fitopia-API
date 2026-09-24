from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "phone_number",
            "username",
            "full_name",
            "password",
            "confirm_password",
            "gender",
            "birth_date",
        )

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "رمزها یکسان نیستند"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """شماره موبایل یا نام کاربری + رمز؛ اختیاری: مرا به خاطر بسپار (۱۰ روز)."""

    username = serializers.CharField(help_text="شماره موبایل یا نام کاربری")
    password = serializers.CharField()
    remember_me = serializers.BooleanField(
        required=False,
        default=False,
        help_text="اگر true باشد، نشست تا ۱۰ روز معتبر می‌ماند",
    )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "username",
            "full_name",
            "gender",
            "birth_date",
            "avatar",
            "is_staff_user",
            "created_at",
        )
        read_only_fields = (
            "id",
            "phone_number",
            "is_staff_user",
            "created_at",
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "full_name",
            "gender",
            "birth_date",
            "avatar",
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "رمزها یکسان نیستند"})
        return attrs
