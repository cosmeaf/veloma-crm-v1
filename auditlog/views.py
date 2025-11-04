from rest_framework import generics, permissions
from .models import AuditEvent
from .serializers import AuditEventSerializer
from .permissions import IsStaffOrAdmin

class AuditEventListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        qs = AuditEvent.objects.all()
        # filtros úteis
        user_id = self.request.query_params.get("user_id")
        if user_id: qs = qs.filter(user_id=user_id)
        action = self.request.query_params.get("action")
        if action: qs = qs.filter(action=action)
        company_nif = self.request.query_params.get("company_nif")
        if company_nif: qs = qs.filter(company_nif=company_nif)
        model = self.request.query_params.get("model")
        if model: qs = qs.filter(model=model)
        path = self.request.query_params.get("path")
        if path: qs = qs.filter(path__icontains=path)
        return qs.order_by("-occurred_at")
