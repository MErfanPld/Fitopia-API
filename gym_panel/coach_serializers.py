from rest_framework import serializers
from gym.models import GymCoach
from .coach_models import (
    CoachStudent, CoachPost, TrainingProgram, TrainingExercise,
    DietProgram, DietMeal, SupplementProgram, SupplementItem, StudentMonthlyStat,
)


class CoachProfileSerializer(serializers.ModelSerializer):
    gym_name = serializers.CharField(source="gym.name", read_only=True)
    sports = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = GymCoach
        fields = ["id", "gym", "gym_name", "full_name", "image", "specialty", "bio", "is_active", "sports"]
        read_only_fields = ["id", "gym", "gym_name", "is_active"]


class CoachProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymCoach
        fields = ["full_name", "image", "specialty", "bio"]


class CoachStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachStudent
        fields = [
            "id", "coach", "gym", "gym_customer", "fitopia_user",
            "full_name", "phone", "gender", "birth_date", "photo",
            "notes", "is_active", "joined_at", "created_at",
        ]
        read_only_fields = ["id", "coach", "gym", "joined_at", "created_at"]


class CoachStudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachStudent
        fields = [
            "gym_customer", "fitopia_user", "full_name", "phone",
            "gender", "birth_date", "photo", "notes", "is_active",
        ]


class CoachPostSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True, default=None)

    class Meta:
        model = CoachPost
        fields = ["id", "coach", "student", "student_name", "image", "caption", "post_type", "is_public", "created_at"]
        read_only_fields = ["id", "coach", "created_at"]


class CoachPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachPost
        fields = ["student", "image", "caption", "post_type", "is_public"]


class TrainingExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingExercise
        fields = ["id", "day_of_week", "exercise_name", "sets", "reps", "rest_seconds", "notes", "order"]


class TrainingProgramSerializer(serializers.ModelSerializer):
    exercises = TrainingExerciseSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = TrainingProgram
        fields = ["id", "coach", "student", "student_name", "title", "description", "year", "month", "status", "exercises", "created_at"]
        read_only_fields = ["id", "coach", "created_at"]


class TrainingProgramWriteSerializer(serializers.ModelSerializer):
    exercises = TrainingExerciseSerializer(many=True, required=False)

    class Meta:
        model = TrainingProgram
        fields = ["student", "title", "description", "year", "month", "status", "exercises"]

    def create(self, validated_data):
        exercises = validated_data.pop("exercises", [])
        program = TrainingProgram.objects.create(**validated_data)
        for ex in exercises:
            TrainingExercise.objects.create(program=program, **ex)
        return program

    def update(self, instance, validated_data):
        exercises = validated_data.pop("exercises", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if exercises is not None:
            instance.exercises.all().delete()
            for ex in exercises:
                TrainingExercise.objects.create(program=instance, **ex)
        return instance


class DietMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietMeal
        fields = ["id", "meal_type", "items", "calories", "order"]


class DietProgramWriteSerializer(serializers.ModelSerializer):
    meals = DietMealSerializer(many=True, required=False)

    class Meta:
        model = DietProgram
        fields = ["student", "title", "description", "year", "month", "daily_calories", "status", "meals"]

    def create(self, validated_data):
        meals = validated_data.pop("meals", [])
        program = DietProgram.objects.create(**validated_data)
        for meal in meals:
            DietMeal.objects.create(program=program, **meal)
        return program

    def update(self, instance, validated_data):
        meals = validated_data.pop("meals", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if meals is not None:
            instance.meals.all().delete()
            for meal in meals:
                DietMeal.objects.create(program=instance, **meal)
        return instance


class DietProgramSerializer(serializers.ModelSerializer):
    meals = DietMealSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = DietProgram
        fields = ["id", "coach", "student", "student_name", "title", "description", "year", "month", "daily_calories", "status", "meals", "created_at"]


class SupplementItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplementItem
        fields = ["id", "name", "dosage", "timing", "notes", "order"]


class SupplementProgramWriteSerializer(serializers.ModelSerializer):
    items = SupplementItemSerializer(many=True, required=False)

    class Meta:
        model = SupplementProgram
        fields = ["student", "title", "description", "year", "month", "status", "items"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        program = SupplementProgram.objects.create(**validated_data)
        for item in items:
            SupplementItem.objects.create(program=program, **item)
        return program

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for item in items:
                SupplementItem.objects.create(program=instance, **item)
        return instance


class SupplementProgramSerializer(serializers.ModelSerializer):
    items = SupplementItemSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = SupplementProgram
        fields = ["id", "coach", "student", "student_name", "title", "description", "year", "month", "status", "items", "created_at"]


class StudentMonthlyStatSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = StudentMonthlyStat
        fields = [
            "id", "coach", "student", "student_name", "year", "month",
            "weight_kg", "body_fat_percent", "muscle_mass_kg",
            "workouts_completed", "adherence_percent", "notes", "measurements",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "coach", "created_at", "updated_at"]
