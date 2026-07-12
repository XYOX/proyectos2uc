from django.contrib import admin
from .models import AreaComun, Reserva


@admin.register(AreaComun)
class AreaComunAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'horario_inicio', 'horario_fin', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id_residente', 'id_area', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'estado')
    list_filter = ('estado',)
    search_fields = ('id_residente__id_usuario__email',)
    ordering = ('-fecha_reserva',)

