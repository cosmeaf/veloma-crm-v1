from rest_framework import serializers
from django.core.files.base import ContentFile
from datetime import date

from .models import Bank, Statement, StatementLine
from .utils import BANK_REGISTRY

class StatementUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    period_tag = serializers.RegexField(r"^\d{4}-\d{2}$", write_only=True)

    def validate(self, attrs):
        bank: Bank = self.context["bank"]
        f = attrs["file"]
        if not f.name.lower().endswith(".pdf"):
            raise serializers.ValidationError({"file": "Envie um PDF."})

        raw = f.read()
        parser = BANK_REGISTRY.get(bank.slug)
        if not parser:
            raise serializers.ValidationError({"bank": "Banco não suportado."})
        try:
            parser.validate_pdf(raw)
        except Exception as e:
            raise serializers.ValidationError({"file": f"PDF inválido: {e}"})
        f.seek(0)
        attrs["raw"] = raw
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        bank: Bank = self.context["bank"]
        f = validated_data["file"]
        raw = validated_data["raw"]
        period_tag = validated_data["period_tag"]

        st = Statement.objects.create(
            user=request.user, bank=bank, period_tag=period_tag, file_name=f.name
        )
        st.pdf.save(f.name, ContentFile(raw), save=True)

        # parse -> linhas
        parser = BANK_REGISTRY[bank.slug]
        rows = parser.extract_transactions(raw)

        yyyy, mm = [int(x) for x in period_tag.split("-")]

        def _to_date(part):
            if not part: return None
            part = part.replace(".", "-").replace("/", "-")
            bits = [int(x) for x in part.split("-") if x]
            if len(bits) == 2:  # dd-mm
                dd, m2 = bits
                use_mm = m2 if 1 <= m2 <= 12 else mm
                return date(yyyy, use_mm, dd)
            if len(bits) == 3:  # dd-mm-yyyy
                dd, m2, y2 = bits
                return date(y2, m2, dd)
            return None

        objs = []
        for r in rows:
            d = _to_date(r.get("date"))
            vd = _to_date(r.get("value_date")) or d
            objs.append(StatementLine(
                statement=st,
                date=d,
                value_date=vd,
                description=(r.get("description") or "")[:512],
                debit=r.get("debit") or 0,
                credit=r.get("credit") or 0,
                balance=r.get("balance"),
            ))
        StatementLine.objects.bulk_create(objs, batch_size=1000)
        return st

class StatementBasicSerializer(serializers.ModelSerializer):
    bank = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    class Meta:
        model = Statement
        fields = ["id", "bank", "period_tag", "file_name", "created_at"]

class StatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementLine
        fields = ["date", "value_date", "description", "debit", "credit", "balance"]

class StatementDetailSerializer(serializers.ModelSerializer):
    bank = serializers.SlugRelatedField(read_only=True, slug_field="slug")
    lines = StatementLineSerializer(many=True, read_only=True)
    class Meta:
        model = Statement
        fields = ["id", "bank", "period_tag", "file_name", "created_at", "lines"]
