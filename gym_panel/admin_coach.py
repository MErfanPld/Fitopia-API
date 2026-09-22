"""Admin registrations for coach domain models (imported from admin.py)."""
from django.contrib import admin

from .coach_models import (
    CoachStudent,
    CoachPost,
    TrainingProgram,
    TrainingExercise,
    DietProgram,
    DietMeal,
    SupplementProgram,
    SupplementItem,
    StudentMonthlyStat,
)


class TrainingExerciseInline(admin.TabularInline):
    model = TrainingExercise
    extra = 1
    fields = ("order", "day_of_week", "exercise_name", "sets", "reps", "rest_seconds", "notes")


class DietMealInline(admin.TabularInline):
    model = DietMeal
    extra = 1
    fields = ("order", "meal_type", "items", "calories")


class SupplementItemInline(admin.TabularInline):
    model = SupplementItem
    extra = 1
    fields = ("order", "name", "dosage", "timing", "notes")


@admin.register(CoachStudent)
class CoachStudentAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "coach",
        "gym",
        "gender",
        "is_active",
        "joined_at",
    )
    list_filter = ("is_active", "gender", "gym")
    search_fields = ("full_name", "phone", "notes")
    autocomplete_fields = ("coach", "gym", "gym_customer", "fitopia_user")
    readonly_fields = ("joined_at", "created_at", "updated_at")


@admin.register(CoachPost)
class CoachPostAdmin(admin.ModelAdmin):
    list_display = ("id", "coach", "post_type", "student", "caption_short", "is_public", "created_at")
    list_filter = ("post_type", "is_public", "created_at")
    search_fields = ("caption", "coach__full_name", "student__full_name")
    autocomplete_fields = ("coach", "student")
    readonly_fields = ("created_at",)

    @admin.display(description="کپشن")
    def caption_short(self, obj):
        return (obj.caption or "")[:50]


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "coach", "year", "month", "status", "created_at")
    list_filter = ("status", "year", "month")
    search_fields = ("title", "student__full_name", "description")
    autocomplete_fields = ("coach", "student")
    inlines = [TrainingExerciseInline]
    readonly_fields = ("created_at",)


@admin.register(DietProgram)
class DietProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "coach", "year", "month", "daily_calories", "status")
    list_filter = ("status", "year", "month")
    search_fields = ("title", "student__full_name")
    autocomplete_fields = ("coach", "student")
    inlines = [DietMealInline]
    readonly_fields = ("created_at",)


@admin.register(SupplementProgram)
class SupplementProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "coach", "year", "month", "status")
    list_filter = ("status", "year", "month")
    search_fields = ("title", "student__full_name")
    autocomplete_fields = ("coach", "student")
    inlines = [SupplementItemInline]
    readonly_fields = ("created_at",)


@admin.register(StudentMonthlyStat)
class StudentMonthlyStatAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "year",
        "month",
        "weight_kg",
        "body_fat_percent",
        "workouts_completed",
        "adherence_percent",
        "coach",
    )
    list_filter = ("year", "month")
    search_fields = ("student__full_name", "notes")
    autocomplete_fields = ("coach", "student")
    readonly_fields = ("created_at", "updated_at")
