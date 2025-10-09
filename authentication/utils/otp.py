from datetime import timedelta
from django.utils import timezone
from authentication.models import OtpCode

def get_or_create_recent_otp(user):
    # Reuso dentro de 60s para evitar spam
    recent = OtpCode.objects.filter(user=user, is_used=False).first()
    if recent and (timezone.now() - recent.created_at).total_seconds() < 60:
        return recent, False
    otp = OtpCode.objects.create(user=user, code=OtpCode.generate_otp())
    return otp, True
