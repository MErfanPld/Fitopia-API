from django.contrib import admin

from .models import HomeSlider


@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):

    list_display = [
        "title",
        "is_active",
        "order",
        "created_at",
    ]

    list_filter = [
        "is_active",
    ]

    search_fields = [
        "title",
        "description",
    ]

    list_editable = [
        "is_active",
        "order",
    ]

    ordering = [
        "order",
        "-created_at",
    ]