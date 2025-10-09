from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .token import TokenObtainPairWithRoleSerializer, TokenRefreshWithRoleSerializer

class TokenObtainPairWithRoleView(TokenObtainPairView):
    serializer_class = TokenObtainPairWithRoleSerializer

class TokenRefreshWithRoleView(TokenRefreshView):
    serializer_class = TokenRefreshWithRoleSerializer
