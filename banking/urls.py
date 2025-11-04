from django.urls import path
from .views import (
    StatementUploadView, StatementListView, StatementDetailView, StatementRenderXLSXView
)

urlpatterns = [
    path("banks/<slug:bank_slug>/statements/", StatementUploadView.as_view(), name="statement-upload"),
    path("banks/<slug:bank_slug>/statements/list/", StatementListView.as_view(), name="statement-list"),
    path("banks/<slug:bank_slug>/statements/<int:pk>/", StatementDetailView.as_view(), name="statement-detail"),
    path("banks/<slug:bank_slug>/statements/<int:pk>/render.xlsx", StatementRenderXLSXView.as_view(), name="statement-render-xlsx"),
]
