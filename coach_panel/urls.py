"""پنل مربی — /api/coach-panel/ — فقط نقش coach"""
from django.urls import path, include
from . import views as v

urlpatterns = [
    path("me/", v.CoachMeView.as_view(), name="cp-me"),

    path("gyms/<int:gym_id>/exercises/", v.ExerciseListCreateView.as_view(), name="cp-exercises"),
    path("gyms/<int:gym_id>/exercises/<int:pk>/", v.ExerciseDetailView.as_view(), name="cp-exercise-detail"),
    path("gyms/<int:gym_id>/workouts/", v.WorkoutListCreateView.as_view(), name="cp-workouts"),
    path("gyms/<int:gym_id>/workouts/<int:pk>/", v.WorkoutDetailView.as_view(), name="cp-workout-detail"),
    path("gyms/<int:gym_id>/prs/", v.PRListCreateView.as_view(), name="cp-prs"),
    path("gyms/<int:gym_id>/prs/<int:pk>/", v.PRDetailView.as_view(), name="cp-pr-detail"),
    path("gyms/<int:gym_id>/progress-photos/", v.ProgressPhotoListCreateView.as_view(), name="cp-progress-photos"),
    path("gyms/<int:gym_id>/progress-photos/<int:pk>/", v.ProgressPhotoDetailView.as_view(), name="cp-progress-photo-detail"),
    path("gyms/<int:gym_id>/progress/", v.ProgressChartView.as_view(), name="cp-progress-chart"),
    path("gyms/<int:gym_id>/leaderboard/", v.LeaderboardView.as_view(), name="cp-leaderboard"),
    path("gyms/<int:gym_id>/feed/", v.FeedListCreateView.as_view(), name="cp-feed"),
    path("gyms/<int:gym_id>/feed/<int:pk>/", v.FeedDetailView.as_view(), name="cp-feed-detail"),
    path("gyms/<int:gym_id>/feed/<int:post_id>/like/", v.FeedLikeToggleView.as_view(), name="cp-feed-like"),
    path("gyms/<int:gym_id>/feed/<int:post_id>/comments/", v.FeedCommentListCreateView.as_view(), name="cp-feed-comments"),
    path("gyms/<int:gym_id>/analytics/", v.AnalyticsView.as_view(), name="cp-analytics"),

    # شاگرد / برنامه / آمار از gym_panel.coach
    path("", include("gym_panel.coach_urls")),
]
