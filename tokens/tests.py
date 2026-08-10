from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from gym.models import Gym
from subscriptions.models import Plan, UserSubscription
from tokens.models import GymToken
from gym_panel.models import GymStaffAccess


class TokenSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="09122220001",
            password="StrongPass123",
        )
        self.staff = User.objects.create_user(
            phone_number="09122220002",
            username="gymstaff",
            password="StrongPass123",
            is_staff_user=True,
        )
        self.gym = Gym.objects.create(
            name="Token Gym",
            address="Addr",
            phone="02100000001",
            latitude=35.7,
            longitude=51.4,
        )
        GymStaffAccess.objects.create(user=self.staff, gym=self.gym, role="owner")
        self.plan = Plan.objects.create(
            name="Token Plan",
            price=100000,
            duration_days=30,
            token_count=5,
        )
        self.plan.gyms.add(self.gym)
        self.sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            paid_amount=100000,
            tokens_total=5,
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_request_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/tokens/request/",
            {"gym_id": self.gym.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.tokens_used, 1)

    def test_request_token_without_subscription(self):
        other = User.objects.create_user(
            phone_number="09122220003", password="StrongPass123"
        )
        self.client.force_authenticate(user=other)
        response = self.client.post(
            "/api/tokens/request/",
            {"gym_id": self.gym.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_and_consume_token(self):
        token = GymToken.objects.create(subscription=self.sub, gym=self.gym)
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            "/api/tokens/validate/",
            {"token_code": str(token.token_code)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        token.refresh_from_db()
        self.assertEqual(token.status, "used")

    def test_double_use_rejected(self):
        token = GymToken.objects.create(subscription=self.sub, gym=self.gym)
        self.client.force_authenticate(user=self.staff)
        self.client.post(
            "/api/tokens/validate/",
            {"token_code": str(token.token_code)},
            format="json",
        )
        response = self.client.post(
            "/api/tokens/validate/",
            {"token_code": str(token.token_code)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["valid"])

    def test_wrong_gym_staff_cannot_validate(self):
        other_gym = Gym.objects.create(
            name="Other",
            address="A",
            phone="02100000002",
            latitude=35.8,
            longitude=51.5,
        )
        other_staff = User.objects.create_user(
            phone_number="09122220004",
            username="otherstaff",
            password="StrongPass123",
            is_staff_user=True,
        )
        GymStaffAccess.objects.create(user=other_staff, gym=other_gym, role="owner")
        token = GymToken.objects.create(subscription=self.sub, gym=self.gym)
        self.client.force_authenticate(user=other_staff)
        response = self.client.post(
            "/api/tokens/validate/",
            {"token_code": str(token.token_code)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_expired_token_rejected(self):
        token = GymToken.objects.create(subscription=self.sub, gym=self.gym)
        GymToken.objects.filter(pk=token.pk).update(
            valid_until=timezone.now() - timedelta(hours=1)
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            "/api/tokens/validate/",
            {"token_code": str(token.token_code)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
