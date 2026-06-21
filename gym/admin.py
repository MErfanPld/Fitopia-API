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


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("name", "phone","latitude", "longitude","is_popular", "popularity_score")
    list_filter = ("is_popular",)
    search_fields = ("name",)
    filter_horizontal = ("sports",)
    inlines = [GymPriceInline,GymImageInline,GymVideoInline]


@admin.register(GymPrice)
class GymPriceAdmin(admin.ModelAdmin):
    list_display = ("gym", "sport", "monthly_price", "yearly_price")
    list_filter = ("sport",)