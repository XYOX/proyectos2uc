from datetime import time, datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Residente
from .models import AreaComun, Reserva


def get_residente_by_user_id(user_id):
    return (
        Residente.objects.filter(id_usuario_id=user_id)
        .select_related("id_usuario")
        .first()
    )


def serialize_area(area):
    return {
        "id": area.id,
        "nombre": area.nombre,
        "descripcion": area.descripcion,
        "capacidad": area.capacidad,
        "horario_inicio": area.horario_inicio.strftime("%H:%M"),
        "horario_fin": area.horario_fin.strftime("%H:%M"),
    }


def serialize_reserva(reserva):
    return {
        "id": reserva.id,
        "residente_id": reserva.id_residente.id_usuario_id,
        "residente_nombre": reserva.id_residente.id_usuario.nombre,
        "area": reserva.id_area.nombre,
        "fecha": (
            reserva.fecha_reserva.isoformat()
            if hasattr(reserva.fecha_reserva, "isoformat")
            else reserva.fecha_reserva
        ),
        "hora_inicio": (
            reserva.hora_inicio.strftime("%H:%M")
            if hasattr(reserva.hora_inicio, "strftime")
            else reserva.hora_inicio
        ),
        "hora_fin": (
            reserva.hora_fin.strftime("%H:%M")
            if hasattr(reserva.hora_fin, "strftime")
            else reserva.hora_fin
        ),
        "estado": reserva.estado,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def areas_view(request):
    areas = AreaComun.objects.filter(activo=True).order_by("nombre")
    return Response([serialize_area(area) for area in areas])


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def reservas_view(request):
    if request.method == "GET":
        residente_id = request.query_params.get("residente_id")
        area_nombre = request.query_params.get("area")
        reservas = Reserva.objects.select_related(
            "id_residente__id_usuario", "id_area"
        ).order_by("-fecha_reserva", "-id")
        if residente_id:
            reservas = reservas.filter(id_residente__id_usuario_id=residente_id)
        if area_nombre:
            reservas = reservas.filter(id_area__nombre=area_nombre)
        return Response([serialize_reserva(r) for r in reservas])

    # POST — crear reserva
    residente = get_residente_by_user_id(request.data.get("residente_id"))
    if not residente:
        return Response(
            {"error": "Residente no encontrado."}, status=status.HTTP_404_NOT_FOUND
        )
    if residente.estado_financiero == "moroso":
        return Response(
            {"error": "Usuario presenta deuda activa. Reserva bloqueada (HU13)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    area = AreaComun.objects.filter(nombre=request.data.get("area")).first()
    if not area:
        return Response(
            {"error": "Área común no encontrada."}, status=status.HTTP_404_NOT_FOUND
        )

    fecha = request.data.get("fecha")
    hora_inicio_str = request.data.get("hora_inicio", "")
    hora_fin_str = request.data.get("hora_fin", "")

    if not hora_inicio_str or not hora_fin_str:
        return Response(
            {"error": "Debe indicar hora de inicio y hora de fin."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        hi = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hf = datetime.strptime(hora_fin_str, "%H:%M").time()
    except ValueError:
        return Response(
            {"error": "Formato de hora inválido. Use HH:MM."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if hi >= hf:
        return Response(
            {"error": "La hora de inicio debe ser anterior a la hora de fin."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validar que el horario esté dentro del rango del área
    if hi < area.horario_inicio or hf > area.horario_fin:
        return Response(
            {
                "error": f'El área solo está disponible de {area.horario_inicio.strftime("%H:%M")} a {area.horario_fin.strftime("%H:%M")}.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validar conflicto de horario: otra reserva activa que se solape
    conflicto = (
        Reserva.objects.filter(
            id_area=area,
            fecha_reserva=fecha,
            estado__in=["confirmada", "pendiente"],
        )
        .filter(
            hora_inicio__lt=hf,
            hora_fin__gt=hi,
        )
        .exists()
    )

    if conflicto:
        return Response(
            {"error": "El área ya tiene una reserva en ese horario. Elige otro turno."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reserva = Reserva.objects.create(
        id_residente=residente,
        id_area=area,
        fecha_reserva=fecha,
        hora_inicio=hi,
        hora_fin=hf,
        estado="confirmada",
        fecha_solicitud=timezone.now(),
    )
    reserva.refresh_from_db()
    return Response(serialize_reserva(reserva), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def cancelar_reserva(request, reserva_id):
    reserva = (
        Reserva.objects.select_related("id_residente__id_usuario", "id_area")
        .filter(pk=reserva_id)
        .first()
    )
    if not reserva:
        return Response(
            {"error": "Reserva no encontrada."}, status=status.HTTP_404_NOT_FOUND
        )
    reserva.estado = "cancelada"
    reserva.save(update_fields=["estado"])
    return Response(serialize_reserva(reserva))
