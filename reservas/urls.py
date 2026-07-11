from django.urls import path

from .views import areas_view, cancelar_reserva, reservas_view

urlpatterns = [
    path('areas/', areas_view, name='areas'),
    path('reservas/', reservas_view, name='reservas'),
    path('reservas/<int:reserva_id>/cancelar/', cancelar_reserva, name='cancelar_reserva'),
]
