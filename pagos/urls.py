from django.urls import path

from .views import pagos_pendientes, pagos_view, validar_pago

urlpatterns = [
    path('pagos/', pagos_view, name='pagos'),
    path('pagos/pendientes/', pagos_pendientes, name='pagos_pendientes'),
    path('pagos/<int:pago_id>/validar/', validar_pago, name='validar_pago'),
]
