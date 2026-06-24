from rest_framework import serializers

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "phone_number",
            "username",
            "full_name",
            "password",
        ]

    def create(self, validated_data):
        return User.objects.create_user(
            phone_number=validated_data.get("phone_number"),
            username=validated_data.get("username"),
            full_name=validated_data.get("full_name", ""),
            password=validated_data["password"],
        )
    
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
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