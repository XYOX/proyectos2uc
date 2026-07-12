from collections import defaultdict
import random
import string

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pagos.models import CuotaMantenimiento, Pago
from usuarios.models import (
    Administrador,
    Invitacion,
    Residente,
    SolicitudRegistro,
    Usuario,
)
from comunicaciones.models import Notificacion

chat_messages = []


@api_view(["GET"])
def hello(request):
    return Response({"message": "CondoAI API 🚀"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reporte_financiero(request):
    todos_pagos = Pago.objects.select_related("id_residente__id_usuario").all()
    aprobados = todos_pagos.filter(estado="aprobado")
    pendientes = todos_pagos.filter(estado="pendiente")
    rechazados = todos_pagos.filter(estado="rechazado")

    total_recaudado = aprobados.aggregate(t=Sum("monto"))["t"] or 0
    total_residentes = Residente.objects.count()
    morosos_qs = Residente.objects.filter(estado_financiero="moroso").select_related(
        "id_usuario"
    )
    morosos_count = morosos_qs.count()
    tasa_morosidad = (
        round((morosos_count / total_residentes * 100), 1) if total_residentes else 0
    )

    # Recaudación por mes — últimos 12 meses completos (incluye meses en cero)
    por_mes = defaultdict(float)
    for p in aprobados:
        mes = p.fecha_pago.strftime("%Y-%m")
        por_mes[mes] += float(p.monto)

    now = timezone.localdate()
    meses_12 = []
    for i in range(11, -1, -1):
        # retroceder i meses desde el mes actual
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        clave = f"{year}-{month:02d}"
        meses_12.append({"mes": clave, "total": por_mes.get(clave, 0.0)})

    # Lista de morosos
    lista_morosos = [
        {
            "nombre": r.id_usuario.nombre,
            "dpto": r.nro_departamento,
        }
        for r in morosos_qs
    ]

    # Mes anterior para calcular variación
    mes_actual = now.strftime("%Y-%m")
    prev_month = now.month - 1 or 12
    prev_year = now.year if now.month > 1 else now.year - 1
    mes_anterior = f"{prev_year}-{prev_month:02d}"
    total_actual = por_mes.get(mes_actual, 0)
    total_anterior = por_mes.get(mes_anterior, 0)
    variacion = (
        round(((total_actual - total_anterior) / total_anterior * 100), 1)
        if total_anterior
        else 0
    )

    return Response(
        {
            "totalRecaudado": float(total_recaudado),
            "cantidadPagos": aprobados.count(),
            "pagosPendientes": pendientes.count(),
            "pagosRechazados": rechazados.count(),
            "morosos": morosos_count,
            "tasaMorosidad": tasa_morosidad,
            "listaMorosos": lista_morosos,
            "recaudacionMensual": meses_12,
            "variacionMesAnterior": variacion,
            "fechaGeneracion": timezone.localtime(timezone.now()).strftime(
                "%d/%m/%Y %H:%M"
            ),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reporte_cobranza(request):
    hoy = timezone.localdate()
    dias_prox = int(request.query_params.get("dias", 7))
    limite_prox = hoy + timezone.timedelta(days=dias_prox)

    cuotas = (
        CuotaMantenimiento.objects.exclude(estado="pagado")
        .select_related("id_residente__id_usuario")
        .order_by("fecha_vencimiento")
    )

    vencidas = []
    proximas = []

    for c in cuotas:
        item = {
            "id": c.id,
            "residente": c.id_residente.id_usuario.nombre,
            "dpto": c.id_residente.nro_departamento,
            "periodo": c.periodo,
            "monto": float(c.monto),
            "fecha_vencimiento": c.fecha_vencimiento.strftime("%d/%m/%Y"),
            "dias_vencido": (
                (hoy - c.fecha_vencimiento).days if c.fecha_vencimiento < hoy else 0
            ),
            "dias_para_vencer": (
                (c.fecha_vencimiento - hoy).days if c.fecha_vencimiento >= hoy else 0
            ),
            "estado": c.estado,
        }
        if c.fecha_vencimiento < hoy:
            vencidas.append(item)
        elif c.fecha_vencimiento <= limite_prox:
            proximas.append(item)

    return Response(
        {
            "fecha": hoy.strftime("%d/%m/%Y"),
            "diasProximidad": dias_prox,
            "totalVencidas": len(vencidas),
            "totalProximas": len(proximas),
            "montoVencido": sum(v["monto"] for v in vencidas),
            "montoProximo": sum(p["monto"] for p in proximas),
            "vencidas": vencidas,
            "proximas": proximas,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def solicitudes_view(request):
    solicitudes = SolicitudRegistro.objects.filter(estado="pendiente").order_by(
        "-fecha_solicitud", "-id"
    )
    return Response(
        [
            {
                "id": solicitud.id,
                "nombre": f"{solicitud.nombres} {solicitud.apellidos}".strip(),
                "email": solicitud.email,
                "dpto": solicitud.dpto_solicitado,
                "telefono": solicitud.telefono,
                "estado": solicitud.estado,
                "fecha": timezone.localtime(solicitud.fecha_solicitud).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "motivo_rechazo": solicitud.motivo_rechazo,
            }
            for solicitud in solicitudes
        ]
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def aprobar_solicitud(request, solicitud_id):
    solicitud = SolicitudRegistro.objects.filter(pk=solicitud_id).first()
    if not solicitud:
        return Response(
            {"error": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND
        )

    usuario = Usuario.objects.filter(email=solicitud.email).first()
    if not usuario:
        return Response(
            {"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
        )

    admin = Administrador.objects.filter(id_usuario=request.user).first()
    solicitud.estado = "aprobado"
    solicitud.id_admin_procesa = admin
    solicitud.save(update_fields=["estado", "id_admin_procesa"])

    usuario.is_active = True
    usuario.save(update_fields=["is_active"])
    Residente.objects.get_or_create(
        id_usuario=usuario,
        defaults={
            "nro_departamento": solicitud.dpto_solicitado or "Sin asignar",
            "estado_financiero": "al_dia",
            "fecha_ingreso": timezone.localdate(),
        },
    )

    return Response({"mensaje": "Solicitud aprobada correctamente."})


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def rechazar_solicitud(request, solicitud_id):
    solicitud = SolicitudRegistro.objects.filter(pk=solicitud_id).first()
    if not solicitud:
        return Response(
            {"error": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND
        )

    admin = Administrador.objects.filter(id_usuario=request.user).first()
    solicitud.estado = "rechazado"
    solicitud.motivo_rechazo = request.data.get("motivo") or "Sin motivo especificado"
    solicitud.id_admin_procesa = admin
    solicitud.save(update_fields=["estado", "motivo_rechazo", "id_admin_procesa"])
    return Response({"mensaje": "Solicitud rechazada correctamente."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def crear_invitacion(request):
    admin = Administrador.objects.filter(id_usuario=request.user).first()
    if not admin:
        return Response(
            {"error": "Solo los administradores pueden generar invitaciones."},
            status=status.HTTP_403_FORBIDDEN,
        )

    dpto = (request.data.get("dpto") or "").strip()
    if not dpto:
        return Response(
            {"error": "El departamento es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    while True:
        codigo = "CONDO-" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        if not Invitacion.objects.filter(codigo=codigo).exists():
            break

    invitacion = Invitacion.objects.create(
        codigo=codigo,
        dpto_destino=dpto,
        usado=False,
        id_admin_creador=admin,
    )
    return Response(
        {
            "id": invitacion.id,
            "codigo": invitacion.codigo,
            "dpto": invitacion.dpto_destino,
            "usado": invitacion.usado,
            "enlace": f"http://127.0.0.1:5500/front/index.html?invitacion={invitacion.codigo}",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_historial(request):
    return Response(chat_messages)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_send(request):
    entry = {
        "id": len(chat_messages) + 1,
        "usuario": request.user.nombre,
        "mensaje": request.data.get("mensaje", ""),
        "fecha": timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M"),
    }
    chat_messages.append(entry)
    return Response(entry, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generar_alertas_morosidad(request):
    hoy = timezone.localdate()

    # Cuotas vencidas pendientes de pago
    cuotas = CuotaMantenimiento.objects.filter(
        estado__in=["pendiente", "vencido"],
        fecha_vencimiento__lt=hoy,
    ).select_related("id_residente__id_usuario")

    creadas = 0
    ya_existentes = 0

    for cuota in cuotas:
        residente = cuota.id_residente
        mensaje = (
            f"Tienes una cuota vencida del período {cuota.periodo} "
            f"por S/ {cuota.monto:.2f} (venció el {cuota.fecha_vencimiento.strftime('%d/%m/%Y')}). "
            f"Por favor regulariza tu pago a la brevedad."
        )
        # Evita duplicar alertas para la misma cuota
        existe = Notificacion.objects.filter(
            id_residente=residente,
            tipo=f"morosidad_cuota_{cuota.id}",
        ).exists()
        if not existe:
            Notificacion.objects.create(
                id_residente=residente,
                tipo=f"morosidad_cuota_{cuota.id}",
                url_accion="#pagos",
            )
            creadas += 1
        else:
            ya_existentes += 1

    return Response(
        {
            "alertas_creadas": creadas,
            "ya_existentes": ya_existentes,
            "total_cuotas_vencidas": cuotas.count(),
        }
    )
