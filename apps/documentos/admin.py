from django.contrib import admin
from .models import DocumentoOficial


@admin.register(DocumentoOficial)
class DocumentoOficialAdmin(admin.ModelAdmin):
    list_display = ["numero_documento", "ticket", "generado_por", "fecha_generacion"]
    readonly_fields = ["numero_documento", "ticket", "generado_por", "fecha_generacion", "archivo_pdf"]
