from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from gym.models import GymCoach
from gym_panel.models import GymStaffAccess
from gym_panel.permissions import has_gym_access


def get_coach_for_user(user, gym_id=None):
    """برگرداندن پروفایل مربی لینک‌شده به کاربر."""
    qs = GymCoach.objects.filter(user=user, is_active=True)
    if gym_id is not None:
        qs = qs.filter(gym_id=gym_id)
    return qs.select_related("gym", "user").first()


def ensure_coach(user, gym_id=None):
    coach = get_coach_for_user(user, gym_id)
    if not coach:
        access_qs = GymStaffAccess.objects.filter(
            user=user, is_active=True, role="coach"
        )
        if gym_id is not None:
            access_qs = access_qs.filter(gym_id=gym_id)
        access = access_qs.select_related("gym").first()
        if not access:
            raise PermissionDenied("شما دسترسی پنل مربی ندارید.")
        coach, _ = GymCoach.objects.get_or_create(
            gym=access.gym,
            user=user,
            defaults={
                "full_name": user.full_name or user.username or "مربی",
                "specialty": "",
                "is_active": True,
            },
        )
    return coach


class IsCoach(BasePermission):
    """کاربر باید is_staff_user باشد و پروفایل/نقش مربی داشته باشد."""

    message = "دسترسی پنل مربی ندارید."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if not getattr(request.user, "is_staff_user", False):
            return False
        gym_id = view.kwargs.get("gym_id")
        if GymCoach.objects.filter(user=request.user, is_active=True).exists():
            if gym_id is None:
                return True
            return GymCoach.objects.filter(
                user=request.user, gym_id=gym_id, is_active=True
            ).exists() or has_gym_access(request.user, gym_id)
        qs = GymStaffAccess.objects.filter(
            user=request.user, is_active=True, role="coach"
        )
        if gym_id is not None:
            qs = qs.filter(gym_id=gym_id)
        return qs.exists()
