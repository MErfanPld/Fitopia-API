"""Standalone GymCoach admin for linking user + is_active."""
from django.contrib import admin

from .models import GymCoach


@admin.register(GymCoach)
class GymCoachAdmin(admin.ModelAdmin):
    list_display = ("full_name", "gym", "user", "specialty", "is_active")
    list_filter = ("is_active", "gym")
    search_fields = ("full_name", "specialty", "bio", "user__username", "user__phone")
    autocomplete_fields = ("gym", "user")
    filter_horizontal = ("sports",) if hasattr(GymCoach, "sports") else ()
