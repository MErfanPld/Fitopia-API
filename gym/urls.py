from django.urls import path
from .views import *

urlpatterns = [
    path("categories/", SportCategoryListView.as_view()),
    path("sports/", SportListView.as_view()),
    path("", GymListView.as_view()),
    path("top/", TopPopularGymsAPIView.as_view(), name="top-gyms"),
    path("nearby/", NearbyGymsAPIView.as_view()),
    path("prices/", GymPriceListView.as_view()),
    path(
        "<int:pk>/",
        GymDetailAPIView.as_view(),
        name="gym-detail",
    ),
]