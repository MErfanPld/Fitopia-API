from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from gym.models import Gym, Sport, SportCategory
from gym_panel.models import (
    GymStaffAccess, GymCustomer, FinanceTransaction,
)


class ManagementExpansionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            phone_number="09130000001", username="owner1",
            password="StrongPass123", is_staff_user=True,
        )
        self.other_owner = User.objects.create_user(
            phone_number="09130000002", username="owner2",
            password="StrongPass123", is_staff_user=True,
        )
        self.gym = Gym.objects.create(
            name="Main Gym", address="A", phone="0211",
            latitude=35.7, longitude=51.4,
        )
        self.other_gym = Gym.objects.create(
            name="Other Gym", address="B", phone="0212",
            latitude=35.8, longitude=51.5,
        )
        GymStaffAccess.objects.create(user=self.owner, gym=self.gym, role="owner")
        GymStaffAccess.objects.create(user=self.other_owner, gym=self.other_gym, role="owner")
        cat = SportCategory.objects.create(title="Cat", slug="cat-mgmt")
        self.sport = Sport.objects.create(category=cat, name="Yoga")
        self.gym.sports.add(self.sport)
        self.customer = GymCustomer.objects.create(
            gym=self.gym, full_name="Ali", phone="09131111111",
            join_date=date.today(), source="manual", added_by=self.owner,
            sessions_total=10, sessions_remaining=10,
        )
        self.client.force_authenticate(user=self.owner)

    def test_create_offering(self):
        response = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/offerings/",
            {
                "sport": self.sport.id,
                "description": "Morning yoga",
                "capacity": 15,
                "single_session_price": 150000,
                "course_price": 2000000,
                "schedules": [
                    {"day_of_week": 0, "start_time": "08:00:00", "end_time": "09:00:00"}
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_course_and_enrollment_capacity(self):
        course_resp = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/courses/",
            {
                "sport": self.sport.id,
                "title": "Yoga 101",
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=30)),
                "capacity": 1,
                "price": 500000,
            },
            format="json",
        )
        self.assertEqual(course_resp.status_code, status.HTTP_201_CREATED)
        course_id = course_resp.data["id"]
        en = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/courses/{course_id}/enroll/",
            {"customer": self.customer.id, "price_paid": 500000},
            format="json",
        )
        self.assertEqual(en.status_code, status.HTTP_201_CREATED)
        c2 = GymCustomer.objects.create(
            gym=self.gym, full_name="Sara", phone="09132222222",
            join_date=date.today(), source="manual",
        )
        en2 = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/courses/{course_id}/enroll/",
            {"customer": c2.id, "price_paid": 500000},
            format="json",
        )
        self.assertEqual(en2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_idor_other_gym_members(self):
        self.client.force_authenticate(user=self.other_owner)
        response = self.client.get(f"/api/gym-panel/gyms/{self.gym.id}/members/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_check_in_out_and_duplicate(self):
        cin = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/attendance/check-in/",
            {"customer_id": self.customer.id, "method": "manual"},
            format="json",
        )
        self.assertEqual(cin.status_code, status.HTTP_201_CREATED)
        dup = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/attendance/check-in/",
            {"customer_id": self.customer.id, "method": "manual"},
            format="json",
        )
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)
        cout = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/attendance/check-out/",
            {"visit_id": cin.data["id"]},
            format="json",
        )
        self.assertEqual(cout.status_code, status.HTTP_200_OK)

    def test_unauthorized_check_in(self):
        self.client.force_authenticate(user=self.other_owner)
        response = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/attendance/check-in/",
            {"customer_id": self.customer.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finance_payment_and_report(self):
        pay = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/finance/payments/",
            {
                "customer": self.customer.id,
                "total_price": 1000000,
                "amount_paid": 400000,
                "discount": 0,
                "description": "partial membership",
            },
            format="json",
        )
        self.assertEqual(pay.status_code, status.HTTP_201_CREATED)
        self.assertEqual(pay.data["remaining_balance"], 600000)
        report = self.client.get(f"/api/gym-panel/gyms/{self.gym.id}/finance/reports/")
        self.assertEqual(report.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(report.data["monthly"]["income"], 400000)

    def test_refund_cannot_exceed(self):
        tx = FinanceTransaction.objects.create(
            gym=self.gym, type="income", category="membership",
            amount=100000, date=date.today(), created_by=self.owner,
        )
        bad = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/finance/refunds/",
            {"original_transaction": tx.id, "amount": 200000, "reason": "too much"},
            format="json",
        )
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finance_idor(self):
        self.client.force_authenticate(user=self.other_owner)
        response = self.client.get(
            f"/api/gym-panel/gyms/{self.gym.id}/finance/transactions/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_single_session_creates_income(self):
        response = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/single-sessions/",
            {"customer": self.customer.id, "sport": self.sport.id, "price": 200000},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_employee_create(self):
        emp_user = User.objects.create_user(
            phone_number="09130000009", username="emp1", password="StrongPass123"
        )
        response = self.client.post(
            f"/api/gym-panel/gyms/{self.gym.id}/employees/",
            {"user": emp_user.id, "role": "receptionist"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
