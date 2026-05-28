"""
Autenticación JWT via httpOnly cookie en lugar del header Authorization.
Esto permite que la PWA Angular use cookies persistentes y seguras (XSS-safe).
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """
    Lee el access token desde la cookie `sigtic_access` (httpOnly).
    Fallback al header Authorization: Bearer <token> para compatibilidad
    con herramientas como Swagger UI.
    """

    def authenticate(self, request):
        cookie_name = getattr(settings, "JWT_COOKIE_NAME", "sigtic_access")
        raw_token = request.COOKIES.get(cookie_name)

        if raw_token is None:
            # Fallback al header estándar (útil en Swagger/Postman)
            return super().authenticate(request)

        try:
            validated_token = self.get_validated_token(raw_token)
        except (TokenError, InvalidToken):
            return None

        try:
            user = self.get_user(validated_token)
        except Exception:
            return None

        return user, validated_token
