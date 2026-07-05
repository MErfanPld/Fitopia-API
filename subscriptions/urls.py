from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    # پلن‌ها
    path("plans/", views.PlanListView.as_view(), name="plan-list"),
    path("plans/<int:pk>/", views.PlanDetailView.as_view(), name="plan-detail"),

    # خرید و مدیریت اشتراک
    path("purchase/", views.PurchaseSubscriptionView.as_view(), name="purchase"),
    path("my/", views.MySubscriptionView.as_view(), name="my-subscription"),
    path("history/", views.MySubscriptionHistoryView.as_view(), name="subscription-history"),

    # تخفیف
    path("my-discount/", views.MyDiscountView.as_view(), name="my-discount"),

    # ادمین
    path("expire/<int:pk>/", views.ExpireSubscriptionView.as_view(), name="expire-subscription"),
    
    path("subscriptions/<int:pk>/gyms/", SubscriptionGymsAPIView.as_view(), name="subscription-gyms"),
    path("subscriptions/me/gyms/", MyActiveSubscriptionGymsAPIView.as_view(), name="my-subscription-gyms"),

]