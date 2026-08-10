from rest_framework.permissions import BasePermission
from .models import GymStaffAccess, StaffPermission

ROLE_DEFAULTS = {
    "owner": {c[0] for c in StaffPermission.CODE_CHOICES},
    "manager": {
        "customer.view", "customer.create", "customer.update",
        "course.view", "course.create", "course.update", "course.enroll",
        "attendance.view", "attendance.create",
        "finance.view", "finance.create", "finance.report",
        "employee.view", "offering.manage",
    },
    "receptionist": {
        "customer.view", "customer.create", "customer.update",
        "course.view", "course.enroll",
        "attendance.view", "attendance.create",
        "finance.create",
    },
    "accountant": {
        "customer.view",
        "finance.view", "finance.create", "finance.update", "finance.report", "finance.refund",
    },
    "coach": {
        "customer.view",
        "course.view", "course.update",
        "attendance.view", "attendance.create",
    },
    "staff": {
        "customer.view", "attendance.view", "attendance.create",
    },
}


class IsGymStaff(BasePermission):
    message = "شما دسترسی باشگاه‌داری ندارید."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_staff_user", False)
        )


def has_gym_access(user, gym_id):
    return GymStaffAccess.objects.filter(
        user=user, gym_id=gym_id, is_active=True
    ).exists()


def get_staff_access(user, gym_id):
    return GymStaffAccess.objects.filter(
        user=user, gym_id=gym_id, is_active=True
    ).first()


def user_has_perm(user, gym_id, code):
    access = get_staff_access(user, gym_id)
    if not access:
        return False
    if access.role == "owner":
        return True
    explicit = set(
        access.permissions.values_list("code", flat=True)
    )
    if explicit:
        return code in explicit
    return code in ROLE_DEFAULTS.get(access.role, set())


class HasGymPermission(BasePermission):
    message = "شما مجوز انجام این عملیات را ندارید."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if not getattr(request.user, "is_staff_user", False):
            return False
        gym_id = view.kwargs.get("gym_id")
        if gym_id is None:
            return True
        code = getattr(view, "required_permission", None)
        if not code:
            return has_gym_access(request.user, gym_id)
        return user_has_perm(request.user, gym_id, code)
