from rest_framework import serializers
from .models import (
    Exercise, WorkoutSession, WorkoutSet, PersonalRecord,
    ProgressPhoto, FeedLike, FeedComment,
)


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id", "gym", "coach", "name", "muscle_group", "equipment",
            "instructions", "video_url", "is_public", "created_at",
        ]
        read_only_fields = ["id", "gym", "coach", "created_at"]


class WorkoutSetSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = WorkoutSet
        fields = [
            "id", "exercise", "exercise_name", "set_number", "reps",
            "weight_kg", "duration_seconds", "rpe", "notes", "order",
        ]


class WorkoutSessionSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, required=False)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    total_volume = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = [
            "id", "coach", "student", "student_name", "gym", "title",
            "performed_at", "duration_minutes", "notes", "feeling",
            "sets", "total_volume", "created_at",
        ]
        read_only_fields = ["id", "coach", "gym", "created_at"]

    def get_total_volume(self, obj):
        total = 0
        for s in obj.sets.all():
            if s.weight_kg and s.reps:
                total += float(s.weight_kg) * s.reps
        return round(total, 2)


class WorkoutSessionWriteSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, required=False)

    class Meta:
        model = WorkoutSession
        fields = [
            "student", "title", "performed_at", "duration_minutes",
            "notes", "feeling", "sets",
        ]

    def create(self, validated_data):
        sets_data = validated_data.pop("sets", [])
        session = WorkoutSession.objects.create(**validated_data)
        for i, s in enumerate(sets_data):
            data = dict(s)
            data.setdefault("order", i)
            WorkoutSet.objects.create(session=session, **data)
        return session

    def update(self, instance, validated_data):
        sets_data = validated_data.pop("sets", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if sets_data is not None:
            instance.sets.all().delete()
            for i, s in enumerate(sets_data):
                data = dict(s)
                data.setdefault("order", i)
                WorkoutSet.objects.create(session=instance, **data)
        return instance


class PersonalRecordSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = PersonalRecord
        fields = [
            "id", "coach", "student", "student_name", "gym", "exercise",
            "exercise_name", "value", "unit", "achieved_at", "notes",
            "workout_set", "created_at",
        ]
        read_only_fields = ["id", "coach", "gym", "created_at"]


class ProgressPhotoSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = ProgressPhoto
        fields = [
            "id", "coach", "student", "student_name", "gym", "image",
            "caption", "side", "taken_at", "weight_kg", "created_at",
        ]
        read_only_fields = ["id", "coach", "gym", "created_at"]


class FeedCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = FeedComment
        fields = ["id", "post", "user", "user_name", "text", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def get_user_name(self, obj):
        u = obj.user
        return getattr(u, "full_name", None) or getattr(u, "username", None) or str(u.id)
