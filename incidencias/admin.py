from django.contrib import admin
from .models import Incidencia, IncidenciaSeguimiento


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'id_residente', 'categoria', 'prioridad', 'estado', 'fecha_creacion')
    list_filter = ('categoria', 'prioridad', 'estado')
    search_fields = ('titulo', 'descripcion', 'id_residente__id_usuario__email')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('clasificacion_ia',)


@admin.register(IncidenciaSeguimiento)
class IncidenciaSeguimientoAdmin(admin.ModelAdmin):
    list_display = ('id_incidencia', 'id_usuario', 'estado_anterior', 'estado_nuevo', 'fecha_registro')
    ordering = ('-fecha_registro',)

