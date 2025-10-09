from django.contrib import admin
from django.urls import path, include
from authentication.views_token import TokenObtainPairWithRoleView, TokenRefreshWithRoleView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView



urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth API
    path("api/auth/login", TokenObtainPairWithRoleView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh", TokenRefreshWithRoleView.as_view(), name="token_refresh"),
    path("api/auth/", include("authentication.urls")),
    # OpenAPI schema e UIs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
