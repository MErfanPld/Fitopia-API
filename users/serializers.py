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
            "gender",
            "birth_date",
            "is_staff_user",
            "is_active",
            "is_staff",
        ]
