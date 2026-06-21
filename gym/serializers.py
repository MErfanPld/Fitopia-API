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

from rest_framework import serializers
from .models import Gym, GymImage, GymVideo


class GymImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymImage
        fields = ["id", "image", "title"]


class GymVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymVideo
        fields = ["id", "video_url", "title"]


class GymSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)
    prices = GymPriceSerializer(many=True, read_only=True)
    images = GymImageSerializer(many=True, read_only=True)
    videos = GymVideoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Gym
        fields = "__all__"