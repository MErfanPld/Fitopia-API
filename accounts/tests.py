from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_with_phone(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "phone_number": "09121111111",
                "full_name": "Test User",
                "password": "StrongPass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertTrue(User.objects.filter(phone_number="09121111111").exists())

    def test_register_requires_identifier(self):
        response = self.client.post(
            "/api/accounts/register/",
            {"password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone(self):
        User.objects.create_user(phone_number="09121111112", password="StrongPass123")
        response = self.client.post(
            "/api/accounts/register/",
            {"phone_number": "09121111112", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_phone(self):
        User.objects.create_user(
            phone_number="09121111113",
            username="user13",
            password="StrongPass123",
        )
        response = self.client.post(
            "/api/accounts/login/",
            {"username": "09121111113", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)

    def test_login_with_username(self):
        User.objects.create_user(
            phone_number="09121111114",
            username="loginuser",
            password="StrongPass123",
        )
        response = self.client.post(
            "/api/accounts/login/",
            {"username": "loginuser", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid_credentials(self):
        User.objects.create_user(phone_number="09121111115", password="StrongPass123")
        response = self.client.post(
            "/api/accounts/login/",
            {"username": "09121111115", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_auth(self):
        response = self.client.get("/api/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_and_change_password(self):
        user = User.objects.create_user(
            phone_number="09121111116",
            password="StrongPass123",
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone_number"], "09121111116")

        response = self.client.post(
            "/api/accounts/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "NewStrong456",
                "confirm_password": "NewStrong456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrong456"))

    def test_logout_blacklists_token(self):
        user = User.objects.create_user(
            phone_number="09121111117",
            password="StrongPass123",
        )
        login = self.client.post(
            "/api/accounts/login/",
            {"username": "09121111117", "password": "StrongPass123"},
            format="json",
        )
        refresh = login.data["tokens"]["refresh"]
        access = login.data["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            "/api/accounts/logout/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
