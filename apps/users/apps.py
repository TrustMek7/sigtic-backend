from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"
    verbose_name = "Usuarios"

    def ready(self):
        try:
            from drf_spectacular.extensions import OpenApiAuthenticationExtension

            class CookieJWTAuthExtension(OpenApiAuthenticationExtension):
                target_class = "apps.users.cookie_auth.CookieJWTAuthentication"
                name = "CookieJWT"

                def get_security_definition(self, auto_schema):
                    return {
                        "type": "apiKey",
                        "in": "cookie",
                        "name": "sigtic_access",
                        "description": (
                            "JWT access token almacenado en httpOnly cookie `sigtic_access`. "
                            "Se setea automáticamente al hacer POST /api/v1/auth/login/. "
                            "En Swagger UI activa 'Include credentials'."
                        ),
                    }
        except ImportError:
            pass
