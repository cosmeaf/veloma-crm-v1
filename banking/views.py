from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from openpyxl import Workbook

from core.permissions import IsOwnerOrStaffOrSuperUser  # seu módulo global
from .models import Bank, Statement
from .serializers import (
    StatementUploadSerializer, StatementBasicSerializer, StatementDetailSerializer
)

class StatementUploadView(APIView):
    """
    POST /api/banks/<bank_slug>/statements/
    body: { file: <pdf>, period_tag: "YYYY-MM" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, bank_slug: str):
        bank = get_object_or_404(Bank, pk=bank_slug, is_active=True)
        s = StatementUploadSerializer(data=request.data, context={"request": request, "bank": bank})
        s.is_valid(raise_exception=True)
        st = s.save()
        return Response(StatementBasicSerializer(st).data, status=status.HTTP_201_CREATED)

class StatementListView(generics.ListAPIView):
    """
    GET /api/banks/<bank_slug>/statements/
    - user: vê os próprios
    - staff/superuser: vê todos do banco
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StatementBasicSerializer

    def get_queryset(self):
        bank = get_object_or_404(Bank, pk=self.kwargs["bank_slug"])
        qs = Statement.objects.filter(bank=bank).order_by("-created_at").select_related("bank", "user")
        u = self.request.user
        if u.is_superuser or u.is_staff:
            return qs
        return qs.filter(user=u)

class StatementDetailView(generics.RetrieveAPIView):
    """
    GET /api/banks/<bank_slug>/statements/<id>/
    - user: somente o próprio
    - staff/superuser: qualquer
    """
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrSuperUser]
    serializer_class = StatementDetailSerializer

    def get_queryset(self):
        bank = get_object_or_404(Bank, pk=self.kwargs["bank_slug"])
        return Statement.objects.filter(bank=bank).select_related("bank", "user").prefetch_related("lines")

class StatementRenderXLSXView(APIView):
    """
    GET /api/banks/<bank_slug>/statements/<id>/render.xlsx
    Gera XLSX em tempo real a partir das linhas (StatementLine).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, bank_slug: str, pk: int):
        st = get_object_or_404(Statement.objects.select_related("bank", "user").prefetch_related("lines"),
                               bank_id=bank_slug, pk=pk)
        u = request.user
        if not (u.is_superuser or u.is_staff or st.user_id == u.id):
            return Response({"detail": "Forbidden."}, status=403)

        # Se precisar usar template XLSX por banco, aqui é o ponto de carregar (load_workbook).
        wb = Workbook()
        ws = wb.active
        headers = ["date", "value_date", "description", "debit", "credit", "balance"]
        ws.append(headers)

        for ln in st.lines.all().iterator():
            ws.append([
                ln.date.isoformat() if ln.date else "",
                ln.value_date.isoformat() if ln.value_date else "",
                ln.description,
                float(ln.debit or 0),
                float(ln.credit or 0),
                float(ln.balance) if ln.balance is not None else "",
            ])

        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)

        resp = HttpResponse(
            bio.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resp["Content-Disposition"] = f'attachment; filename="{st.bank_id}_{st.period_tag}_{st.id}.xlsx"'
        return resp
