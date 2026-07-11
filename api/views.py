import random
import string

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pagos.models import Pago
from usuarios.models import Administrador, Invitacion, Residente, SolicitudRegistro, Usuario

chat_messages = []


@api_view(['GET'])
def hello(request):
    return Response({'message': 'CondoAI API 🚀'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_financiero(request):
    pagos_aprobados = Pago.objects.filter(estado='aprobado')
    total_recaudado = pagos_aprobados.aggregate(total=Sum('monto'))['total'] or 0
    morosos = Residente.objects.filter(estado_financiero='moroso').count()
    return Response({
        'totalRecaudado': float(total_recaudado),
        'cantidadPagos': pagos_aprobados.count(),
        'morosos': morosos,
        'fechaGeneracion': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M'),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def solicitudes_view(request):
    solicitudes = SolicitudRegistro.objects.filter(estado='pendiente').order_by('-fecha_solicitud', '-id')
    return Response([
        {
            'id': solicitud.id,
            'nombre': f'{solicitud.nombres} {solicitud.apellidos}'.strip(),
            'email': solicitud.email,
            'dpto': solicitud.dpto_solicitado,
            'telefono': solicitud.telefono,
            'estado': solicitud.estado,
            'fecha': timezone.localtime(solicitud.fecha_solicitud).strftime('%Y-%m-%d %H:%M'),
            'motivo_rechazo': solicitud.motivo_rechazo,
        }
        for solicitud in solicitudes
    ])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def aprobar_solicitud(request, solicitud_id):
    solicitud = SolicitudRegistro.objects.filter(pk=solicitud_id).first()
    if not solicitud:
        return Response({'error': 'Solicitud no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    usuario = Usuario.objects.filter(email=solicitud.email).first()
    if not usuario:
        return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    admin = Administrador.objects.filter(id_usuario=request.user).first()
    solicitud.estado = 'aprobado'
    solicitud.id_admin_procesa = admin
    solicitud.save(update_fields=['estado', 'id_admin_procesa'])

    usuario.is_active = True
    usuario.save(update_fields=['is_active'])
    Residente.objects.get_or_create(
        id_usuario=usuario,
        defaults={
            'nro_departamento': solicitud.dpto_solicitado or 'Sin asignar',
            'estado_financiero': 'al_dia',
            'fecha_ingreso': timezone.localdate(),
        },
    )

    return Response({'mensaje': 'Solicitud aprobada correctamente.'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def rechazar_solicitud(request, solicitud_id):
    solicitud = SolicitudRegistro.objects.filter(pk=solicitud_id).first()
    if not solicitud:
        return Response({'error': 'Solicitud no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    admin = Administrador.objects.filter(id_usuario=request.user).first()
    solicitud.estado = 'rechazado'
    solicitud.motivo_rechazo = request.data.get('motivo') or 'Sin motivo especificado'
    solicitud.id_admin_procesa = admin
    solicitud.save(update_fields=['estado', 'motivo_rechazo', 'id_admin_procesa'])
    return Response({'mensaje': 'Solicitud rechazada correctamente.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_invitacion(request):
    admin = Administrador.objects.filter(id_usuario=request.user).first()
    if not admin:
        return Response({'error': 'Solo los administradores pueden generar invitaciones.'}, status=status.HTTP_403_FORBIDDEN)

    dpto = (request.data.get('dpto') or '').strip()
    if not dpto:
        return Response({'error': 'El departamento es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

    while True:
        codigo = 'CONDO-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Invitacion.objects.filter(codigo=codigo).exists():
            break

    invitacion = Invitacion.objects.create(
        codigo=codigo,
        dpto_destino=dpto,
        usado=False,
        id_admin_creador=admin,
    )
    return Response({
        'id': invitacion.id,
        'codigo': invitacion.codigo,
        'dpto': invitacion.dpto_destino,
        'usado': invitacion.usado,
        'enlace': f'http://127.0.0.1:5500/front/index.html?invitacion={invitacion.codigo}',
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_historial(request):
    return Response(chat_messages)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_send(request):
    entry = {
        'id': len(chat_messages) + 1,
        'usuario': request.user.nombre,
        'mensaje': request.data.get('mensaje', ''),
        'fecha': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M'),
    }
    chat_messages.append(entry)
    return Response(entry, status=status.HTTP_201_CREATED)
