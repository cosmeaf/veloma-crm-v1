# authentication/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiExample  # <-- imports corretos

from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserRecoverySerializer,
    UserOtpVerifySerializer,
    ResetPasswordSerializer,
    EmailSendVerificationSerializer,
    EmailVerifySerializer,
)

# ---- Throttles (NÃO decorar com extend_schema) ----
class RegisterAnonThrottle(AnonRateThrottle):
    scope = "auth_register"

class LoginAnonThrottle(AnonRateThrottle):
    scope = "auth_login"

class RecoveryAnonThrottle(AnonRateThrottle):
    scope = "auth_recovery"

class OtpAnonThrottle(AnonRateThrottle):
    scope = "auth_otp"


# ------------------------- Register -------------------------
@extend_schema(
    tags=["Auth"],
    request=UserRegisterSerializer,
    responses={201: UserRegisterSerializer},
    examples=[
        OpenApiExample(
            "Exemplo de registro",
            value={
                "username": "123456789",
                "first_name": "Ana",
                "last_name": "Silva",
                "email": "ana@exemplo.pt",
                "password": "S3nh@forte!",
                "password2": "S3nh@forte!"
            },
            request_only=True,
        )
    ],
)
class UserRegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer
    throttle_classes = [RegisterAnonThrottle]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_201_CREATED)


# ------------------------- Login -------------------------
@extend_schema(
    tags=["Auth"],
    request=UserLoginSerializer,
    examples=[
        OpenApiExample(
            "Login por NIF",
            value={"identifier": "123456789", "password": "S3nh@forte!"},
            request_only=True,
        ),
        OpenApiExample(
            "Login por e-mail",
            value={"identifier": "ana@exemplo.pt", "password": "S3nh@forte!"},
            request_only=True,
        ),
    ],
    # responses inferidos do serializer (200 OK)
)
class UserLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    throttle_classes = [LoginAnonThrottle]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        return Response(ser.validated_data, status=status.HTTP_200_OK)


# ------------------------- Recovery -------------------------
@extend_schema(
    tags=["Auth"],
    request=UserRecoverySerializer,
    examples=[
        OpenApiExample(
            "Recovery",
            value={"email": "ana@exemplo.pt"},
            request_only=True,
        ),
    ],
)
class UserRecoveryView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRecoverySerializer
    throttle_classes = [RecoveryAnonThrottle]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_200_OK)


# O resto das views segue igual; se quiser, também decore:
@extend_schema(tags=["Auth"], request=UserRecoverySerializer)
class UserOtpGenerateView(UserRecoveryView):
    throttle_classes = [OtpAnonThrottle]


@extend_schema(tags=["Auth"], request=UserOtpVerifySerializer)
class UserOtpVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserOtpVerifySerializer
    throttle_classes = [OtpAnonThrottle]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        return Response(ser.validated_data, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"], request=ResetPasswordSerializer)
class UserResetPasswordView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"], request=EmailSendVerificationSerializer)
class EmailSendVerificationView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailSendVerificationSerializer

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"], request=EmailVerifySerializer)
class EmailVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailVerifySerializer

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_200_OK)
