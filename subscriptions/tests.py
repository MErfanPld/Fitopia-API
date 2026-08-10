from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from gym.models import Gym
from subscriptions.models import Plan, UserSubscription


class SubscriptionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="09123330001",
            password="StrongPass123",
        )
        self.gym = Gym.objects.create(
            name="Sub Gym",
            address="Addr",
            phone="02110000001",
            latitude=35.7,
            longitude=51.4,
        )
        self.plan = Plan.objects.create(
            name="Monthly",
            price=200000,
            duration_days=30,
            token_count=10,
        )
        self.plan.gyms.add(self.gym)
        self.client.force_authenticate(user=self.user)

    def test_list_plans(self):
        response = self.client.get("/api/subscriptions/plans/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_purchase_subscription(self):
        response = self.client.post(
            "/api/subscriptions/purchase/",
            {"plan_id": self.plan.id, "use_discount": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            UserSubscription.objects.filter(
                user=self.user, status="active"
            ).count(),
            1,
        )

    def test_purchase_cancels_previous_active(self):
        old = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            paid_amount=200000,
            tokens_total=10,
            end_date=timezone.now() + timedelta(days=30),
        )
        response = self.client.post(
            "/api/subscriptions/purchase/",
            {"plan_id": self.plan.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        old.refresh_from_db()
        self.assertEqual(old.status, "cancelled")
        self.assertEqual(
            UserSubscription.objects.filter(
                user=self.user, status="active"
            ).count(),
            1,
        )

    def test_my_subscription(self):
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            paid_amount=200000,
            tokens_total=10,
            end_date=timezone.now() + timedelta(days=30),
        )
        response = self.client.get("/api/subscriptions/my/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tokens_total"], 10)

    def test_my_subscription_none(self):
        response = self.client.get("/api/subscriptions/my/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
