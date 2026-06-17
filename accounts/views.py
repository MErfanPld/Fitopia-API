from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import (
    LogoutSerializer,
    RegisterSerializer,
    LoginSerializer,
)

from users.serializers import UserSerializer
# from .utils import send_sms
# from .models import PasswordResetCode

User = get_user_model()


# =========================
# 🔐 TOKEN HELPER
# =========================
def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# =========================
# 👤 REGISTER
# =========================
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        self.tokens = get_tokens(user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = self.tokens
        return response


# =========================
# 🔐 LOGIN
# =========================
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "شماره/نام کاربری یا رمز اشتباه است"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response({
            "tokens": get_tokens(user),
            "user": UserSerializer(user).data,
            "is_staff_user": user.is_staff_user
        })


# =========================
# 🚪 LOGOUT
# =========================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "توکن اجباری است"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)

            # ❌ این خط را حذف کن (علت 500)
            token.blacklist()

            return Response(
                {"message": "خروج موفق"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# # =========================
# # 🔑 CHANGE PASSWORD
# # =========================
# class ChangePasswordView(APIView):
#     permission_classes = [IsAuthenticated]

#     @extend_schema(
#         request=ChangePasswordSerializer,
#         examples=[
#             OpenApiExample(
#                 "مثال تغییر پسورد",
#                 value={
#                     "old_password": "12345678",
#                     "new_password": "newpass123",
#                     "confirm_password": "newpass123",
#                 },
#                 request_only=True,
#             )
#         ],
#     )
#     def post(self, request):
#         serializer = ChangePasswordSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = request.user
#         old_password = serializer.validated_data["old_password"]
#         new_password = serializer.validated_data["new_password"]

#         if not user.check_password(old_password):
#             return Response(
#                 {"detail": "پسورد فعلی اشتباه است"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         user.set_password(new_password)
#         user.save()

#         return Response({"detail": "پسورد تغییر کرد"}, status=200)


# # =========================
# # 📩 SEND RESET CODE
# # =========================
# class SendResetCodeView(generics.GenericAPIView):
#     serializer_class = SendResetCodeSerializer
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = serializer.validated_data["user"]

#         reset_code = PasswordResetCode.generate_code(user)
#         send_sms(user.phone_number, reset_code.code)

#         return Response({"message": "کد ارسال شد"}, status=200)


# # =========================
# # ✅ VERIFY CODE
# # =========================
# class VerifyResetCodeView(generics.GenericAPIView):
#     serializer_class = VerifyResetCodeSerializer
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         return Response({"message": "کد صحیح است"}, status=200)


# # =========================
# # 🔁 RESET PASSWORD
# # =========================
# class ResetPasswordView(generics.GenericAPIView):
#     serializer_class = ResetPasswordSerializer
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = serializer.validated_data["user"]
#         new_password = serializer.validated_data["password"]

#         user.password = make_password(new_password)
#         user.save()

#         PasswordResetCode.objects.filter(user=user).delete()

#         return Response({"message": "رمز تغییر کرد"}, status=200)