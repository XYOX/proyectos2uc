from django.contrib import admin
from .models import Comunicacion, ComunicacionDestinatario, Notificacion, Documento


@admin.register(Comunicacion)
class ComunicacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_envio')
    list_filter = ('tipo',)
    search_fields = ('titulo',)


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id_residente', 'tipo', 'leido', 'fecha_lectura')
    list_filter = ('leido',)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha_publicacion')
    search_fields = ('titulo',)

