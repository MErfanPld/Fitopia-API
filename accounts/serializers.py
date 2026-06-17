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