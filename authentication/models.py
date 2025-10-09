import uuid
import random
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class OtpCodeQuerySet(models.QuerySet):
    def valid(self):
        expiration_time = timezone.now() - timedelta(minutes=OtpCode.EXPIRES_MINUTES)
        return self.filter(is_used=False, created_at__gte=expiration_time)

    def clean_expired(self):
        expiration_time = timezone.now() - timedelta(minutes=OtpCode.EXPIRES_MINUTES)
        return self.filter(
            models.Q(created_at__lt=expiration_time) | models.Q(is_used=True)
        ).delete()


class OtpCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    EXPIRES_MINUTES = getattr(settings, "OTP_EXPIRES_MINUTES", 10)
    objects = OtpCodeQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["user", "is_used"]),
        ]
        constraints = [models.UniqueConstraint(fields=["user", "code"], name="uniq_user_code")]

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def is_valid(self) -> bool:
        return (
            not self.is_used
            and timezone.now() - self.created_at <= timedelta(minutes=self.EXPIRES_MINUTES)
        )

    def mark_as_used(self, save: bool = True):
        self.is_used = True
        if save:
            self.save(update_fields=["is_used"])

    @staticmethod
    def generate_otp() -> str:
        return "".join(random.choices("0123456789", k=6))


class ResetPasswordToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    EXPIRES_MINUTES = getattr(settings, "RESET_TOKEN_EXPIRES_MINUTES", 30)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.token}"

    def is_valid(self) -> bool:
        return timezone.now() - self.created_at <= timedelta(minutes=self.EXPIRES_MINUTES)


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="email_verify_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    EXPIRES_HOURS = getattr(settings, "EMAIL_VERIFY_EXPIRES_HOURS", 48)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.token}"

    def is_valid(self) -> bool:
        return (timezone.now() - self.created_at) <= timedelta(hours=self.EXPIRES_HOURS)
