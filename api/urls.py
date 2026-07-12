from django.urls import path

from .views import (
    aprobar_solicitud,
    chat_historial,
    chat_send,
    crear_invitacion,
    generar_alertas_morosidad,
    hello,
    reporte_cobranza,
    rechazar_solicitud,
    reporte_financiero,
    solicitudes_view,
)

urlpatterns = [
    path("", hello, name="api_root"),
    path("reportes/financiero/", reporte_financiero, name="reporte_financiero"),
    path("reportes/cobranza/", reporte_cobranza, name="reporte_cobranza"),
    path(
        "reportes/alertas-morosidad/",
        generar_alertas_morosidad,
        name="generar_alertas_morosidad",
    ),
    path("solicitudes/", solicitudes_view, name="solicitudes"),
    path(
        "solicitudes/<int:solicitud_id>/aprobar/",
        aprobar_solicitud,
        name="aprobar_solicitud",
    ),
    path(
        "solicitudes/<int:solicitud_id>/rechazar/",
        rechazar_solicitud,
        name="rechazar_solicitud",
    ),
    path("invitaciones/", crear_invitacion, name="crear_invitacion"),
    path("chat/historial/", chat_historial, name="chat_historial"),
    path("chat/", chat_send, name="chat_send"),
]
