# authentication/token.py
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.utils.roles import infer_role
from authentication.utils.common import user_payload


class TokenObtainPairWithRoleSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = infer_role(user)  # claim no refresh (e propagará pro access)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)  # 'access' e 'refresh'
        u = self.user
        data["user"] = {**user_payload(u), "role": infer_role(u)}
        return data


class TokenRefreshWithRoleSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # Gera access normalmente
        data = super().validate(attrs)

        # Reavalia role no servidor e re-assina o access com claim atualizado
        refresh = RefreshToken(attrs["refresh"])
        user_id = refresh.get("user_id")  # padrão do SimpleJWT

        User = get_user_model()
        try:
            u = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Se não achar, mantém o retorno padrão
            return data

        # Recria o access a partir do refresh e injeta role atual
        new_access = refresh.access_token
        new_access["role"] = infer_role(u)
        data["access"] = str(new_access)

        # Conveniência para o front (opcional, mas útil):
        data["user"] = {**user_payload(u), "role": infer_role(u)}
        return data
