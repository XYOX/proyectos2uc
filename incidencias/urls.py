from django.urls import path

from .views import asignar_incidencia, cerrar_incidencia, incidencias_view

urlpatterns = [
    path('incidencias/', incidencias_view, name='incidencias'),
    path('incidencias/<int:incidencia_id>/asignar/', asignar_incidencia, name='asignar_incidencia'),
    path('incidencias/<int:incidencia_id>/cerrar/', cerrar_incidencia, name='cerrar_incidencia'),
]
