from django.contrib import admin
from .models import Sede, UnidadOrganica, Subgerencia, Dependencia


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "direccion", "sed_ide_siggo"]
    search_fields = ["nombre"]


class SubgerenciaInline(admin.TabularInline):
    model = Subgerencia
    extra = 0


@admin.register(UnidadOrganica)
class UnidadOrganicaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "abreviatura", "nivel", "superior"]
    search_fields = ["nombre", "abreviatura"]
    inlines = [SubgerenciaInline]


class DependenciaInline(admin.TabularInline):
    model = Dependencia
    extra = 0


@admin.register(Subgerencia)
class SubgerenciaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "unidad_organica"]
    list_filter = ["unidad_organica"]
    inlines = [DependenciaInline]


@admin.register(Dependencia)
class DependenciaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "subgerencia"]
    list_filter = ["subgerencia"]
