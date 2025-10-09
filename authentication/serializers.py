from __future__ import annotations
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import (
    OtpCode,
    ResetPasswordToken,
    EmailVerificationToken,
)
from authentication.utils.nif import normalize_nif, validate_pt_nif
from authentication.utils.common import clean_email, ensure_group, user_payload
from authentication.utils.links import reset_password_link
from authentication.utils.otp import get_or_create_recent_otp
from authentication.utils.roles import infer_role
from services.utils.emails.email_service import EmailService

User = get_user_model()


# ---------- Register ----------
class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)  # NIF
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "password2"]

    def validate_username(self, value):
        try:
            nif = normalize_nif(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        if not validate_pt_nif(nif):
            raise serializers.ValidationError("NIF inválido.")
        if User.objects.filter(username=nif).exists():
            raise serializers.ValidationError("NIF já cadastrado.")
        return nif

    def validate_email(self, value):
        email = clean_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Este e-mail já está em uso.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs

    @transaction.atomic
    def create(self, validated):
        validated.pop("password2", None)
        user = User.objects.create_user(
            username=validated["username"],  # NIF
            first_name=validated["first_name"].strip(),
            last_name=validated["last_name"].strip(),
            email=clean_email(validated["email"]),
            password=validated["password"],
        )

        # welcome
        EmailService(
            subject="Bem-vindo(a) à plataforma",
            to_email=user.email,
            template_name="emails/welcome",
            context={"user": user},
        ).send()

        # email de verificação
        from django.conf import settings
        if getattr(settings, "AUTH_REQUIRE_EMAIL_VERIFICATION", True):
            vtoken = EmailVerificationToken.objects.create(user=user)
            req = self.context.get("request")
            # aqui você pode usar uma rota de frontend para verificar; reuso reset_password_link pelo teu util
            verify_link = reset_password_link(req, str(vtoken.token))  # ajuste para AUTH_VERIFY_PATH se preferir
            EmailService(
                subject="Confirme seu e-mail",
                to_email=user.email,
                template_name="emails/email_verify",
                context={"user": user, "verify_link": verify_link},
            ).send()

        refresh = RefreshToken.for_user(user)
        payload = user_payload(user)
        payload["role"] = infer_role(user)
        return {**payload, "access": str(refresh.access_token), "refresh": str(refresh)}


# ---------- Login por NIF ou e-mail (se quiser manter) ----------
class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data["identifier"].strip()
        pwd = data["password"]

        username = None
        if "@" in identifier:
            u = User.objects.filter(email__iexact=clean_email(identifier)).first()
            if u:
                username = u.username
        else:
            try:
                username = normalize_nif(identifier)
            except ValueError:
                pass

        if not username:
            raise serializers.ValidationError("Credenciais inválidas.")

        user = authenticate(username=username, password=pwd)
        if not user:
            raise serializers.ValidationError("Credenciais inválidas.")

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # alerta de login opcional via setting
        from django.conf import settings
        if getattr(settings, "AUTH_LOGIN_ALERT_EMAIL", False):
            req = self.context.get("request")
            ip = req.META.get("REMOTE_ADDR") if req else None
            ua = req.META.get("HTTP_USER_AGENT") if req else None
            EmailService(
                subject="Alerta de login detectado",
                to_email=user.email,
                template_name="emails/login_alert",
                context={"user": user, "ip": ip, "user_agent": ua, "when": timezone.now()},
            ).send()

        ref = RefreshToken.for_user(user)
        payload = user_payload(user)
        payload["role"] = infer_role(user)
        return {"access": str(ref.access_token), "refresh": str(ref), "user": payload}


# ---------- Recovery ----------
class UserRecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = clean_email(value)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError("E-mail não encontrado.")
        self.context["user_obj"] = user
        return email

    def create(self, validated):
        user: User = self.context["user_obj"]
        otp, _created = get_or_create_recent_otp(user)
        EmailService(
            subject="Código de Recuperação",
            to_email=user.email,
            template_name="emails/password_recovery",
            context={"user": user, "otp_code": otp.code},
        ).send()
        return {"detail": "Código enviado para o e-mail cadastrado."}


# ---------- OTP Verify ----------
class UserOtpVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        code = data["code"]
        try:
            otp = OtpCode.objects.filter(code=code, is_used=False).latest("created_at")
        except OtpCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Código inválido ou expirado."})

        if not otp.is_valid():
            otp.delete()
            raise serializers.ValidationError({"code": "Código expirado."})

        otp.is_used = True
        otp.save(update_fields=["is_used"])
        rtoken = ResetPasswordToken.objects.create(user=otp.user)

        request = self.context.get("request")
        return {"reset_url": reset_password_link(request, str(rtoken.token))}


# ---------- Reset Password ----------
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        try:
            rtoken = ResetPasswordToken.objects.get(token=data["token"])
        except ResetPasswordToken.DoesNotExist:
            raise serializers.ValidationError("Token inválido ou expirado.")
        if not rtoken.is_valid():
            raise serializers.ValidationError("Token expirado.")
        self.context["rtoken"] = rtoken
        return data

    @transaction.atomic
    def create(self, validated):
        rtoken: ResetPasswordToken = self.context["rtoken"]
        user = rtoken.user
        user.set_password(validated["password"])
        user.save(update_fields=["password"])
        rtoken.delete()

        EmailService(
            subject="Senha alterada com sucesso",
            to_email=user.email,
            template_name="emails/password_changed",
            context={"user": user, "changed_at": timezone.now()},
        ).send()

        return {"message": "Senha redefinida com sucesso!"}


# ---------- Email verification ----------
class EmailSendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = clean_email(value)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError("E-mail não encontrado.")
        self.context["user_obj"] = user
        return email

    def create(self, validated):
        user: User = self.context["user_obj"]
        last = EmailVerificationToken.objects.filter(user=user).first()
        reuse = False
        if last and (timezone.now() - last.created_at).total_seconds() < 60:
            vtoken = last
            reuse = True
        else:
            vtoken = EmailVerificationToken.objects.create(user=user)

        req = self.context.get("request")
        verify_link = reset_password_link(req, str(vtoken.token))  # ajuste path se preferir
        EmailService(
            subject="Confirme seu e-mail",
            to_email=user.email,
            template_name="emails/email_verify",
            context={"user": user, "verify_link": verify_link},
        ).send()

        return {"detail": "E-mail de verificação enviado.", "reused": reuse}


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate(self, data):
        try:
            vtoken = EmailVerificationToken.objects.get(token=data["token"])
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Token inválido ou expirado.")

        if not vtoken.is_valid():
            vtoken.delete()
            raise serializers.ValidationError("Token expirado.")

        EmailVerificationToken.objects.filter(user=vtoken.user).delete()
        self.context["user_id"] = vtoken.user_id
        return data

    def create(self, validated):
        return {"detail": "E-mail verificado com sucesso."}
