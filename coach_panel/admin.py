from django.contrib import admin

from .models import (
    Exercise,
    WorkoutSession,
    WorkoutSet,
    PersonalRecord,
    ProgressPhoto,
    FeedLike,
    FeedComment,
)


class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 1
    autocomplete_fields = ("exercise",)
    fields = (
        "order",
        "exercise",
        "set_number",
        "reps",
        "weight_kg",
        "duration_seconds",
        "rpe",
        "notes",
    )


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "equipment", "gym", "coach", "is_public", "created_at")
    list_filter = ("muscle_group", "is_public", "gym")
    search_fields = ("name", "equipment", "instructions")
    autocomplete_fields = ("gym", "coach")
    readonly_fields = ("created_at",)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "student",
        "coach",
        "gym",
        "performed_at",
        "duration_minutes",
        "feeling",
    )
    list_filter = ("gym", "performed_at")
    search_fields = ("title", "student__full_name", "notes")
    autocomplete_fields = ("coach", "student", "gym")
    date_hierarchy = "performed_at"
    inlines = [WorkoutSetInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "exercise", "set_number", "reps", "weight_kg", "rpe")
    list_filter = ("exercise",)
    search_fields = ("exercise__name", "session__title")
    autocomplete_fields = ("session", "exercise")


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exercise",
        "value",
        "unit",
        "achieved_at",
        "coach",
        "gym",
    )
    list_filter = ("unit", "gym", "achieved_at")
    search_fields = ("student__full_name", "exercise__name", "notes")
    autocomplete_fields = ("coach", "student", "gym", "exercise", "workout_set")
    date_hierarchy = "achieved_at"
    readonly_fields = ("created_at",)


@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ("student", "side", "taken_at", "weight_kg", "coach", "gym", "created_at")
    list_filter = ("side", "gym", "taken_at")
    search_fields = ("student__full_name", "caption")
    autocomplete_fields = ("coach", "student", "gym")
    date_hierarchy = "taken_at"
    readonly_fields = ("created_at",)


@admin.register(FeedLike)
class FeedLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__phone", "post__caption")
    autocomplete_fields = ("post", "user")
    readonly_fields = ("created_at",)


@admin.register(FeedComment)
class FeedCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "text_short", "created_at")
    list_filter = ("created_at",)
    search_fields = ("text", "user__username", "user__phone")
    autocomplete_fields = ("post", "user")
    readonly_fields = ("created_at",)

    @admin.display(description="متن")
    def text_short(self, obj):
        return (obj.text or "")[:60]
