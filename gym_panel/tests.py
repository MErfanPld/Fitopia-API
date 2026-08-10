from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from gym.models import Gym
from gym_panel.models import GymStaffAccess, GymCustomer
from datetime import date


class GymCustomerUpdateDeleteRegressionTests(TestCase):
    """Regression: GymCustomerUpdateDeleteView must work after removing duplicate code."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            phone_number="09120000010",
            username="gym_owner",
            password="testpass123",
            is_staff_user=True,
        )
        self.other = User.objects.create_user(
            phone_number="09120000011",
            username="other_owner",
            password="testpass123",
            is_staff_user=True,
        )
        self.gym = Gym.objects.create(
            name="Owner Gym",
            address="Addr",
            phone="02166666666",
            latitude=35.7,
            longitude=51.4,
        )
        self.other_gym = Gym.objects.create(
            name="Other Gym",
            address="Addr2",
            phone="02177777777",
            latitude=35.8,
            longitude=51.5,
        )
        GymStaffAccess.objects.create(user=self.owner, gym=self.gym, role="owner")
        GymStaffAccess.objects.create(user=self.other, gym=self.other_gym, role="owner")

        self.customer = GymCustomer.objects.create(
            gym=self.gym,
            full_name="Test Customer",
            phone="09121111111",
            join_date=date.today(),
            source="manual",
            added_by=self.owner,
        )

    def test_owner_can_retrieve_customer(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/gym-panel/gyms/{self.gym.id}/customers/{self.customer.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["full_name"], "Test Customer")

    def test_owner_can_update_customer(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/gym-panel/gyms/{self.gym.id}/customers/{self.customer.id}/"
        response = self.client.patch(url, {"full_name": "Updated Name"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, "Updated Name")

    def test_other_owner_cannot_access_customer(self):
        self.client.force_authenticate(user=self.other)
        url = f"/api/gym-panel/gyms/{self.gym.id}/customers/{self.customer.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
