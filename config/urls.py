from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("api/v1/auth/", include("apps.users.urls")),

    # Módulos
    path("api/v1/organizacion/", include("apps.organizacion.urls")),
    path("api/v1/catalogo/", include("apps.catalogo.urls")),
    path("api/v1/inventario/", include("apps.inventario.urls")),
    path("api/v1/almacen/", include("apps.almacen.urls")),
    path("api/v1/tickets/", include("apps.tickets.urls")),
    # documentos incluido bajo api/v1/ para gestionar:
    #   POST api/v1/tickets/<pk>/documento/
    #   GET  api/v1/documentos/<pk>/descargar/
    path("api/v1/", include("apps.documentos.urls")),

    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
