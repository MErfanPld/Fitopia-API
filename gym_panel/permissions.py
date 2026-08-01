from rest_framework.permissions import BasePermission
from .models import GymStaffAccess


class IsGymStaff(BasePermission):
    """فقط کاربرانی که is_staff_user=True هستن اجازه دارن"""
    message = "شما دسترسی باشگاه‌داری ندارید."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_staff_user", False)
        )


def has_gym_access(user, gym_id):
    """چک می‌کنه این کاربر به این gym خاص دسترسی داره یا نه"""
    return GymStaffAccess.objects.filter(user=user, gym_id=gym_id).exists()