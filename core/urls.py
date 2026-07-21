from django.urls import path

from .views import HomeSliderAPIView


urlpatterns = [
    path(
        "home-sliders/",
        HomeSliderAPIView.as_view(),
        name="home-sliders"
    ),
]