from django.urls import path
from .views import GenerarDocumentoView, DescargarDocumentoView

urlpatterns = [
    path("tickets/<int:pk>/documento/", GenerarDocumentoView.as_view(), name="generar-documento"),
    path("documentos/<int:pk>/descargar/", DescargarDocumentoView.as_view(), name="descargar-documento"),
]
