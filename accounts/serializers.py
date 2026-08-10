from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "phone_number",
            "username",
            "full_name",
            "password",
        ]

    def validate(self, attrs):
        phone = attrs.get("phone_number")
        username = attrs.get("username")
        if not phone and not username:
            raise serializers.ValidationError(
                "حداقل یکی از شماره موبایل یا نام کاربری الزامی است."
            )
        password = attrs.get("password")
        if password:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("این شماره موبایل قبلاً ثبت شده است.")
        return value

    def validate_username(self, value):
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            phone_number=validated_data.get("phone_number"),
            username=validated_data.get("username"),
            full_name=validated_data.get("full_name", ""),
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    """Accept either phone_number or username as the identifier field 'username'."""
    username = serializers.CharField(
        help_text="شماره موبایل یا نام کاربری"
    )
    password = serializers.CharField()


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

    def validate_username(self, value):
        if value:
            qs = User.objects.filter(username=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "رمز جدید و تکرار آن یکسان نیستند."}
            )
        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return attrs
