from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.perfil_usuario, name='perfil_usuario'),
]
