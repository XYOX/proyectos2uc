from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Residente, Administrador, Invitacion, SolicitudRegistro


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('email', 'nombre', 'apellidos', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_active')
    search_fields = ('email', 'nombre', 'apellidos')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellidos', 'tipo_documento', 'numero_documento', 'fecha_nacimiento')}),
        ('Permisos', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'nombre', 'apellidos', 'rol', 'password1', 'password2')}),
    )


@admin.register(Residente)
class ResidenteAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nro_departamento', 'estado_financiero')
    search_fields = ('id_usuario__email', 'id_usuario__nombre', 'nro_departamento')
    list_filter = ('estado_financiero',)


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'cargo')
    search_fields = ('id_usuario__email', 'id_usuario__nombre')


@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'dpto_destino', 'usado', 'fecha_creacion')
    list_filter = ('usado',)
    search_fields = ('codigo', 'dpto_destino')


@admin.register(SolicitudRegistro)
class SolicitudRegistroAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'email', 'estado', 'fecha_solicitud')
    list_filter = ('estado',)
    search_fields = ('nombres', 'apellidos', 'email')

