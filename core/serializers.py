from rest_framework import serializers
from .models import HomeSlider


class HomeSliderSerializer(serializers.ModelSerializer):

    class Meta:
        model = HomeSlider
        fields = [
            "id",
            "title",
            "description",
            "image",
            "url",
            "button_text",
            "is_active",
            "order",
            "created_at",
            "updated_at",
        ]