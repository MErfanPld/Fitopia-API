from django.urls import path
from . import views

app_name = "tokens"

urlpatterns = [
    # کاربر
    path("request/", views.RequestGymTokenView.as_view(), name="request-token"),
    path("my/", views.MyGymTokensView.as_view(), name="my-tokens"),
    path("my/active/", views.MyActiveTokensView.as_view(), name="my-active-tokens"),

    # باشگاه (اسکن QR)
    path("validate/", views.ValidateGymTokenView.as_view(), name="validate-token"),
]