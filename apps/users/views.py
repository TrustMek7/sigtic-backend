from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, EncargadoActivo, RolSigtic
from .permissions import _get_profile, EsAdmin, EsJefeOEncargado, EsJefe
from .serializers import (
    LoginSerializer,
    UserProfileSerializer,
    UserProfileListSerializer,
    EncargadoActivoSerializer,
    RolUpdateSerializer,
)


def _set_tokens_in_cookies(response, refresh):
    access = refresh.access_token
    access_cookie = getattr(settings, "JWT_COOKIE_NAME", "sigtic_access")
    refresh_cookie = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "sigtic_refresh")
    secure = getattr(settings, "JWT_COOKIE_SECURE", False)
    samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "Lax")

    response.set_cookie(
        key=access_cookie,
        value=str(access),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=int(access.lifetime.total_seconds()),
    )
    response.set_cookie(
        key=refresh_cookie,
        value=str(refresh),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=int(refresh.lifetime.total_seconds()),
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Credenciales inválidas o usuario inactivo."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # SiggoAuthBackend guarda el perfil en user._sigtic_profile al autenticar.
        # Si autenticó por ModelBackend (superuser Django sin bdsiggo), lo creamos.
        profile = getattr(user, "_sigtic_profile", None)

        if profile is None and user.is_superuser:
            # ID negativo para no colisionar con IDs reales de bdsiggo (siempre positivos)
            profile, _ = UserProfile.objects.get_or_create(
                usu_ide_siggo=-(user.pk),
                defaults={
                    "per_ide_siggo": 0,
                    "dni": "00000000",
                    "nombre_completo": user.get_full_name() or user.username,
                    "email": user.email or "",
                    "rol": RolSigtic.ADMIN,
                    "activo": True,
                },
            )

        if not profile or not profile.activo:
            return Response(
                {"detail": "Cuenta inactiva o sin perfil. Contacte al administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        # Embed rol in token claims for quick frontend reads
        refresh["rol"] = profile.rol
        refresh["nombre"] = profile.nombre_completo

        response = Response(
            {
                "id": profile.id,
                "nombre_completo": profile.nombre_completo,
                "rol": profile.rol,
                "rol_display": profile.get_rol_display(),
            },
            status=status.HTTP_200_OK,
        )
        _set_tokens_in_cookies(response, refresh)
        return response


@extend_schema(tags=["Autenticacion"], request=None, responses={200: OpenApiResponse(description="Sesion cerrada. Cookies borradas.")}, summary="Cierra sesion y elimina las cookies JWT")
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_cookie = getattr(settings, "JWT_COOKIE_NAME", "sigtic_access")
        refresh_cookie = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "sigtic_refresh")

        try:
            raw_refresh = request.COOKIES.get(refresh_cookie)
            if raw_refresh:
                token = RefreshToken(raw_refresh)
                token.blacklist()
        except Exception:
            pass

        response = Response({"detail": "Sesión cerrada."}, status=status.HTTP_200_OK)
        response.delete_cookie(access_cookie)
        response.delete_cookie(refresh_cookie)
        return response


@extend_schema(tags=["Autenticacion"], request=None, responses={200: OpenApiResponse(description="Nuevo access token seteado en cookie.")}, summary="Renueva el access token usando la cookie de refresh")
class TokenRefreshCookieView(APIView):
    """Emite nuevo access token leyendo el refresh token desde la cookie."""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "sigtic_refresh")
        raw_refresh = request.COOKIES.get(refresh_cookie)

        if not raw_refresh:
            return Response(
                {"detail": "No se encontró refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(raw_refresh)
        except Exception:
            return Response(
                {"detail": "Refresh token inválido o expirado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_cookie = getattr(settings, "JWT_COOKIE_NAME", "sigtic_access")
        secure = getattr(settings, "JWT_COOKIE_SECURE", False)
        samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "Lax")
        access = refresh.access_token

        response = Response({"detail": "Token renovado."}, status=status.HTTP_200_OK)
        response.set_cookie(
            key=access_cookie,
            value=str(access),
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=int(access.lifetime.total_seconds()),
        )
        return response


class MeView(RetrieveUpdateAPIView):
    """Perfil del usuario autenticado. GET=detalle, PATCH=actualizar sede."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        profile = _get_profile(self.request)
        if profile is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Perfil no encontrado.")
        return profile


class UserProfileListView(ListAPIView):
    """Lista de todos los UserProfiles (solo IT staff)."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileListSerializer

    def get_queryset(self):
        qs = UserProfile.objects.select_related("cargo_principal").order_by("nombre_completo")
        activo = self.request.query_params.get("activo")
        rol = self.request.query_params.get("rol")
        if activo is not None:
            qs = qs.filter(activo=activo.lower() in ("true", "1", "yes"))
        if rol:
            qs = qs.filter(rol=rol.upper())
        return qs

    def get_permissions(self):
        from .permissions import EsInformatica
        return [IsAuthenticated(), EsInformatica()]


class UserProfileDetailView(RetrieveUpdateAPIView):
    """Detalle y actualización de rol de un UserProfile (solo JEFE/ADMIN)."""
    serializer_class = UserProfileSerializer
    http_method_names = ["get", "patch", "head", "options"]
    queryset = UserProfile.objects.select_related("cargo_principal", "sede")

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT"):
            return [IsAuthenticated(), EsJefe()]
        from .permissions import EsInformatica
        return [IsAuthenticated(), EsInformatica()]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            # Only allow rol update via this endpoint
            return RolUpdateSerializer
        return UserProfileSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)


@extend_schema_view(
    get=extend_schema(tags=["Usuarios"], responses=EncargadoActivoSerializer(many=True), summary="Lista encargados activos e historicos"),
    post=extend_schema(tags=["Usuarios"], request=EncargadoActivoSerializer, responses={201: EncargadoActivoSerializer}, summary="Crea un nuevo encargado temporal"),
)
class EncargadoActivoListCreateView(APIView):
    """Lista encargados activos y permite crear uno nuevo (solo JEFE/ADMIN)."""
    permission_classes = [IsAuthenticated, EsJefe]

    def get(self, request):
        encargados = EncargadoActivo.objects.select_related(
            "encargado", "autorizado_por"
        ).order_by("-desde")
        serializer = EncargadoActivoSerializer(encargados, many=True)
        return Response(serializer.data)

    def post(self, request):
        profile = _get_profile(request)
        data = request.data.copy()
        data.setdefault("autorizado_por", profile.id)
        data.setdefault("activo", True)

        serializer = EncargadoActivoSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(tags=["Usuarios"], responses=EncargadoActivoSerializer, summary="Detalle de un encargado"),
    patch=extend_schema(tags=["Usuarios"], request=EncargadoActivoSerializer, responses=EncargadoActivoSerializer, summary="Actualiza datos del encargado"),
    delete=extend_schema(tags=["Usuarios"], responses={204: None}, summary="Desactiva el encargado temporal"),
)
class EncargadoActivoDetailView(APIView):
    """Detalle y desactivación de un encargado (solo JEFE/ADMIN)."""
    permission_classes = [IsAuthenticated, EsJefe]

    def _get_object(self, pk):
        try:
            return EncargadoActivo.objects.select_related("encargado", "autorizado_por").get(pk=pk)
        except EncargadoActivo.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Encargado no encontrado.")

    def get(self, request, pk):
        encargado = self._get_object(pk)
        return Response(EncargadoActivoSerializer(encargado).data)

    def patch(self, request, pk):
        encargado = self._get_object(pk)
        serializer = EncargadoActivoSerializer(
            encargado, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        """Desactiva el encargado (soft delete)."""
        encargado = self._get_object(pk)
        encargado.activo = False
        encargado.hasta = timezone.now()
        encargado.save(update_fields=["activo", "hasta"])
        return Response(status=status.HTTP_204_NO_CONTENT)
