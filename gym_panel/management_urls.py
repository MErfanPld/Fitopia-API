from django.urls import path
from . import management_views as v
from tokens import staff_views as token_staff

urlpatterns = [
    path("gyms/<int:gym_id>/offerings/", v.OfferingListCreateView.as_view()),
    path("gyms/<int:gym_id>/offerings/<int:pk>/", v.OfferingDetailView.as_view()),
    path("gyms/<int:gym_id>/courses/", v.CourseListCreateView.as_view()),
    path("gyms/<int:gym_id>/courses/<int:pk>/", v.CourseDetailView.as_view()),
    path("gyms/<int:gym_id>/courses/<int:course_id>/enroll/", v.CourseEnrollView.as_view()),
    path("gyms/<int:gym_id>/members/", v.CustomerExpandedListCreateView.as_view()),
    path("gyms/<int:gym_id>/members/<int:pk>/", v.CustomerExpandedDetailView.as_view()),
    path("gyms/<int:gym_id>/single-sessions/", v.SingleSessionListCreateView.as_view()),
    path("gyms/<int:gym_id>/employees/", v.EmployeeListCreateView.as_view()),
    path("gyms/<int:gym_id>/employees/<int:pk>/", v.EmployeeDetailView.as_view()),
    path("gyms/<int:gym_id>/employees/<int:pk>/permissions/", v.EmployeePermissionsView.as_view()),
    path("gyms/<int:gym_id>/attendance/check-in/", v.CheckInView.as_view()),
    path("gyms/<int:gym_id>/attendance/check-out/", v.CheckOutView.as_view()),
    path("gyms/<int:gym_id>/attendance/", v.AttendanceListView.as_view()),
    path("gyms/<int:gym_id>/attendance/stats/", v.AttendanceStatsView.as_view()),
    path("gyms/<int:gym_id>/finance/transactions/", v.FinanceTransactionListCreateView.as_view()),
    path("gyms/<int:gym_id>/finance/payments/", v.CustomerPaymentListCreateView.as_view()),
    path("gyms/<int:gym_id>/finance/refunds/", v.RefundCreateView.as_view()),
    path("gyms/<int:gym_id>/finance/reports/", v.FinanceReportView.as_view()),
    path("gyms/<int:gym_id>/audit-logs/", v.AuditLogListView.as_view()),

    # توکن ورود — باشگاه‌دار
    path(
        "gyms/<int:gym_id>/tokens/lookup/",
        token_staff.GymTokenLookupView.as_view(),
        name="gym-token-lookup",
    ),
    path(
        "gyms/<int:gym_id>/tokens/admit/",
        token_staff.GymTokenAdmitView.as_view(),
        name="gym-token-admit",
    ),
    path(
        "gyms/<int:gym_id>/tokens/today/",
        token_staff.GymTokenTodayAdmissionsView.as_view(),
        name="gym-token-today",
    ),
]
