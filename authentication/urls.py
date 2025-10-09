from django.urls import path
from .views import (
    UserRegisterView,
    UserLoginView,
    UserRecoveryView,
    UserOtpGenerateView,
    UserOtpVerifyView,
    UserResetPasswordView,
    EmailSendVerificationView,
    EmailVerifyView,
)
from .views_token import TokenObtainPairWithRoleView, TokenRefreshWithRoleView

urlpatterns = [
    # fluxo próprio
    path("register", UserRegisterView.as_view(), name="auth-register"),
    path("login-legacy", UserLoginView.as_view(), name="auth-login-legacy"),

    path("recovery", UserRecoveryView.as_view(), name="auth-recovery"),
    path("otp/generate", UserOtpGenerateView.as_view(), name="auth-otp-generate"),
    path("otp/verify", UserOtpVerifyView.as_view(), name="auth-otp-verify"),
    path("reset-password", UserResetPasswordView.as_view(), name="auth-reset-password"),

    path("email/send-verification", EmailSendVerificationView.as_view(), name="auth-email-send-verification"),
    path("email/verify", EmailVerifyView.as_view(), name="auth-email-verify"),

    # SimpleJWT com role no token
    path("login", TokenObtainPairWithRoleView.as_view(), name="token_obtain_pair"),
    path("refresh", TokenRefreshWithRoleView.as_view(), name="token_refresh"),
]
