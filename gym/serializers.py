from rest_framework import serializers
from .models import *


class SportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SportCategory
        fields = "__all__"


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = "__all__"


class GymFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = GymFacility
        fields = "__all__"


class GymPriceSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)

    class Meta:
        model = GymPrice
        fields = "__all__"


class GymImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymImage
        fields = "__all__"


class GymVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymVideo
        fields = "__all__"


class GymBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymBanner
        fields = "__all__"


class GymCoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymCoach
        fields = "__all__"


class GymReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymReview
        fields = "__all__"


class GymSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)
    facilities = GymFacilitySerializer(many=True, read_only=True)
    class Meta:
        model = Gym
        fields = "__all__"


class GymDetailSerializer(serializers.ModelSerializer):

    sports = SportSerializer(many=True)

    facilities = GymFacilitySerializer(many=True)

    prices = GymPriceSerializer(many=True)

    images = GymImageSerializer(many=True)

    videos = GymVideoSerializer(many=True)

    banners = GymBannerSerializer(many=True)

    coaches = GymCoachSerializer(many=True)

    reviews = GymReviewSerializer(many=True)

    average_rating = serializers.ReadOnlyField()

    google_map_url = serializers.ReadOnlyField()

    class Meta:
        model = Gym

        fields = (
            "id",
            "name",
            "description",
            "address",
            "phone",
            "latitude",
            "longitude",
            "cover_image",
            "working_hours",
            "rules",
            "instagram",
            "telegram",
            "website",
            "whatsapp",
            "is_popular",
            "popularity_score",
            "average_rating",
            "google_map_url",
            "sports",
            "facilities",
            "prices",
            "images",
            "videos",
            "banners",
            "coaches",
            "reviews",
        )