from django.contrib import admin
from .models import *


@admin.register(SportCategory)
class SportCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title",)


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name",)

class GymPriceInline(admin.TabularInline):
    model = GymPrice
    extra = 1


class GymImageInline(admin.TabularInline):
    model = GymImage
    extra = 1


class GymVideoInline(admin.TabularInline):
    model = GymVideo
    extra = 1


class GymBannerInline(admin.TabularInline):
    model = GymBanner
    extra = 1


class GymCoachInline(admin.TabularInline):
    model = GymCoach
    extra = 1


class GymReviewInline(admin.TabularInline):
    model = GymReview
    extra = 0


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "is_popular",
        "popularity_score"
    )

    filter_horizontal = (
        "sports",
        "facilities"
    )

    inlines = [
        GymPriceInline,
        GymImageInline,
        GymVideoInline,
        GymBannerInline,
        GymCoachInline,
        GymReviewInline,
    ]


admin.site.register(GymFacility)