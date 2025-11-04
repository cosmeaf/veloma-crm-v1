from django.conf import settings
from django.db import models

class Bank(models.Model):
    """
    Cadastre 'millennium' e 'bpi' via Django Admin (slug, name, is_active=True).
    """
    slug = models.SlugField(primary_key=True)  # "millennium" | "bpi" | ...
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

def statement_pdf_path(instance, filename):
    return f"statements/{instance.bank_id}/{instance.user_id}/{instance.period_tag}/{filename}"

class Statement(models.Model):
    """
    Upload original (PDF) + período (YYYY-MM).
    As linhas parseadas ficam em StatementLine.
    O XLSX é gerado on-demand a partir de StatementLine (sem reprocessar PDF).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT)
    period_tag = models.CharField(max_length=7, help_text="YYYY-MM", db_index=True)
    pdf = models.FileField(upload_to=statement_pdf_path)
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["bank", "period_tag", "user"])]

    def __str__(self):
        return f"{self.bank_id} {self.period_tag} ({self.id})"

class StatementLine(models.Model):
    """
    Linhas normalizadas. Base para render do XLSX em tempo real.
    """
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE, related_name="lines")
    date = models.DateField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=512)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["statement"])]
