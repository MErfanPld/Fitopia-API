from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "username",
            "full_name",
            "is_staff_user",
            "is_active",
            "is_staff",
        ]
                
        
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "username",
            "password",
        ]

    def create(self, validated_data):
        return User.objects.create_user(
            phone_number=validated_data.get("phone_number"),
            username=validated_data.get("username"),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            image=validated_data.get("image"),
        )
        
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
        ]
        
        
        
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "username",
            "is_staff_user",
            "is_staff",
            "is_superuser",
            "created_at",
        ]
        read_only_fields = [
            "phone_number",
            "username",
            "is_staff_user",
            "is_staff",
            "is_superuser",
            "created_at",
        ]