from datetime import time

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Residente
from .models import AreaComun, Reserva


def get_residente_by_user_id(user_id):
    return Residente.objects.filter(id_usuario_id=user_id).select_related('id_usuario').first()


def serialize_area(area):
    return {
        'id': area.id,
        'nombre': area.nombre,
        'descripcion': area.descripcion,
        'capacidad': area.capacidad,
    }


def serialize_reserva(reserva):
    return {
        'id': reserva.id,
        'residente_id': reserva.id_residente.id_usuario_id,
        'area': reserva.id_area.nombre,
        'fecha': reserva.fecha_reserva.isoformat() if hasattr(reserva.fecha_reserva, 'isoformat') else reserva.fecha_reserva,
        'hora_inicio': reserva.hora_inicio.strftime('%H:%M') if hasattr(reserva.hora_inicio, 'strftime') else reserva.hora_inicio,
        'hora_fin': reserva.hora_fin.strftime('%H:%M') if hasattr(reserva.hora_fin, 'strftime') else reserva.hora_fin,
        'estado': reserva.estado,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def areas_view(request):
    areas = AreaComun.objects.filter(activo=True).order_by('nombre')
    return Response([serialize_area(area) for area in areas])


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def reservas_view(request):
    if request.method == 'GET':
        residente_id = request.query_params.get('residente_id')
        reservas = Reserva.objects.select_related('id_residente__id_usuario', 'id_area').order_by('-fecha_reserva', '-id')
        if residente_id:
            reservas = reservas.filter(id_residente__id_usuario_id=residente_id)
        return Response([serialize_reserva(reserva) for reserva in reservas])

    residente = get_residente_by_user_id(request.data.get('residente_id'))
    if not residente:
        return Response({'error': 'Residente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if residente.estado_financiero == 'moroso':
        return Response({'error': 'Usuario presenta deuda activa. Reserva bloqueada (HU13).'}, status=status.HTTP_400_BAD_REQUEST)

    area = AreaComun.objects.filter(nombre=request.data.get('area')).first()
    if not area:
        return Response({'error': 'Área común no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    fecha = request.data.get('fecha')
    ocupado = Reserva.objects.filter(id_area=area, fecha_reserva=fecha).exclude(estado='cancelada').exists()
    if ocupado:
        return Response({'error': 'El área ya está reservada en esa fecha.'}, status=status.HTTP_400_BAD_REQUEST)

    reserva = Reserva.objects.create(
        id_residente=residente,
        id_area=area,
        fecha_reserva=fecha,
        hora_inicio=time(10, 0),
        hora_fin=time(12, 0),
        estado='confirmada',
        fecha_solicitud=timezone.now(),
    )
    reserva.refresh_from_db()
    return Response(serialize_reserva(reserva), status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancelar_reserva(request, reserva_id):
    reserva = Reserva.objects.select_related('id_residente__id_usuario', 'id_area').filter(pk=reserva_id).first()
    if not reserva:
        return Response({'error': 'Reserva no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    reserva.estado = 'cancelada'
    reserva.save(update_fields=['estado'])
    return Response(serialize_reserva(reserva))
