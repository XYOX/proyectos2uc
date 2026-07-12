from django.contrib import admin
from .models import CuotaMantenimiento, Pago


@admin.register(CuotaMantenimiento)
class CuotaMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('id_residente', 'periodo', 'monto', 'fecha_vencimiento', 'estado')
    list_filter = ('estado',)
    search_fields = ('id_residente__id_usuario__email', 'periodo')
    ordering = ('-fecha_vencimiento',)


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id_residente', 'id_cuota', 'monto', 'fecha_pago', 'estado')
    list_filter = ('estado',)
    search_fields = ('id_residente__id_usuario__email',)
    ordering = ('-fecha_pago',)

