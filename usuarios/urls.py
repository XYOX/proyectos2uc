from django.urls import path

from .views import perfil_usuario, registro_usuario

urlpatterns = [
    path('usuarios/me/', perfil_usuario, name='perfil_usuario'),
    path('auth/registro/', registro_usuario, name='registro_usuario'),
]
