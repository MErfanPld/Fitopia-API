from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from users.models import User
from gym.models import Gym, SportCategory, Sport
from subscriptions.models import Plan, UserSubscription


class NearbyGymsRegressionTests(TestCase):
    """Regression: NearbyGyms must return ALL matching gyms, not only the first."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="09120000001",
            username="nearby_user",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.gym1 = Gym.objects.create(
            name="Gym Near 1",
            address="Addr 1",
            phone="02111111111",
            latitude=35.7000,
            longitude=51.4000,
        )
        self.gym2 = Gym.objects.create(
            name="Gym Near 2",
            address="Addr 2",
            phone="02122222222",
            latitude=35.7050,
            longitude=51.4050,
        )
        self.gym_far = Gym.objects.create(
            name="Gym Far",
            address="Addr Far",
            phone="02133333333",
            latitude=36.5000,
            longitude=52.5000,
        )

    def test_nearby_returns_multiple_gyms(self):
        response = self.client.get(
            "/api/gym/nearby/",
            {"lat": "35.7000", "lon": "51.4000", "radius": "10"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        names = {item["name"] for item in data}
        self.assertIn("Gym Near 1", names)
        self.assertIn("Gym Near 2", names)
        self.assertNotIn("Gym Far", names)
        self.assertGreaterEqual(len(data), 2)

    def test_nearby_requires_lat_lon(self):
        response = self.client.get("/api/gym/nearby/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GymSportsAccessRegressionTests(TestCase):
    """Regression: GymSportsAccess must not crash on plan.sports (field does not exist)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="09120000002",
            username="sports_user",
            password="testpass123",
        )
        category = SportCategory.objects.create(title="Fitness", slug="fitness")
        self.sport = Sport.objects.create(category=category, name="Bodybuilding")
        self.gym = Gym.objects.create(
            name="Sports Gym",
            address="Addr",
            phone="02144444444",
            latitude=35.7,
            longitude=51.4,
        )
        self.gym.sports.add(self.sport)

        self.plan = Plan.objects.create(
            name="Basic",
            price=100000,
            duration_days=30,
            token_count=10,
        )
        self.plan.gyms.add(self.gym)

        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            paid_amount=100000,
            tokens_total=10,
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_sports_access_no_crash_anonymous(self):
        response = self.client.get(f"/api/gym/{self.gym.id}/sports-access/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("sports", data)
        self.assertEqual(len(data["sports"]), 1)
        self.assertFalse(data["sports"][0]["has_access"])

    def test_sports_access_with_subscription(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/gym/{self.gym.id}/sports-access/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["sports"][0]["has_access"])
        self.assertIsNotNone(data["subscription"])


class SportCoachesRegressionTests(TestCase):
    """Regression: SportCoaches must not crash on plan.sports."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="09120000003",
            username="coach_user",
            password="testpass123",
        )
        category = SportCategory.objects.create(title="Fitness2", slug="fitness2")
        self.sport = Sport.objects.create(category=category, name="Yoga")
        self.gym = Gym.objects.create(
            name="Coach Gym",
            address="Addr",
            phone="02155555555",
            latitude=35.7,
            longitude=51.4,
        )
        self.gym.sports.add(self.sport)

        self.plan = Plan.objects.create(
            name="Pro",
            price=200000,
            duration_days=30,
            token_count=20,
        )
        self.plan.gyms.add(self.gym)

        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            paid_amount=200000,
            tokens_total=20,
            end_date=timezone.now() + timedelta(days=30),
        )

    def test_sport_coaches_no_crash(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/gym/{self.gym.id}/sport/{self.sport.id}/coaches/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("coaches", data)
        self.assertIn("sport", data)
