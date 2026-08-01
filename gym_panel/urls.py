from django.urls import path
from .views import (
    GymCoachListCreateView,
    GymCoachUpdateDeleteView,
    GymPanelLoginView,
    MyGymsView,
    GymPanelUpdateView,
    GymFieldEditRequestView,
    SuggestNewSportView,
    MyChangeRequestsView,
    GymPriceListCreateView,
    GymPriceUpdateDeleteView,
    TicketDetailView,
    TicketMessageCreateView,
)

urlpatterns = [
    path("auth/login/", GymPanelLoginView.as_view(), name="gym-panel-login"),
    path("gyms/", MyGymsView.as_view(), name="gym-panel-my-gyms"),

    path("gyms/<int:gym_id>/update/", GymPanelUpdateView.as_view(), name="gym-panel-update"),
    path("gyms/<int:gym_id>/change-requests/", GymFieldEditRequestView.as_view(), name="gym-panel-field-request"),
    path("gyms/<int:gym_id>/change-requests/list/", MyChangeRequestsView.as_view(), name="gym-panel-my-requests"),
    path("gyms/<int:gym_id>/suggest-sport/", SuggestNewSportView.as_view(), name="gym-panel-suggest-sport"),
    path("gyms/<int:gym_id>/coaches/", GymCoachListCreateView.as_view(), name="gym-panel-coaches"),
    path("gyms/<int:gym_id>/coaches/<int:pk>/", GymCoachUpdateDeleteView.as_view(), name="gym-panel-coach-detail"),

    path("gyms/<int:gym_id>/tickets/<int:pk>/", TicketDetailView.as_view(), name="gym-panel-ticket-detail"),
    path("gyms/<int:gym_id>/tickets/<int:ticket_id>/messages/", TicketMessageCreateView.as_view(), name="gym-panel-ticket-message"),

    path("gyms/<int:gym_id>/prices/", GymPriceListCreateView.as_view(), name="gym-panel-prices"),
    path("gyms/<int:gym_id>/prices/<int:pk>/", GymPriceUpdateDeleteView.as_view(), name="gym-panel-price-detail"),
]