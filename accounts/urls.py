from django.urls import path
from .views import RegisterView, LoginView,LogoutView, UserProfileAPIView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path(
        "profile/",
        UserProfileAPIView.as_view(),
        name="user-profile",
    ),
]

