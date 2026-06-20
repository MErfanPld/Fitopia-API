from rest_framework import serializers
from .models import SportCategory, Sport, Gym, GymPrice


class SportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SportCategory
        fields = "__all__"


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = "__all__"


class GymPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymPrice
        fields = "__all__"


class GymSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)
    prices = GymPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Gym
        fields = "__all__"