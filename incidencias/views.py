from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Residente
from .models import Incidencia, IncidenciaSeguimiento


def get_residente_by_user_id(user_id):
    return Residente.objects.filter(id_usuario_id=user_id).select_related('id_usuario').first()


def clasificar_incidencia(descripcion):
    texto = (descripcion or '').lower()
    categoria = 'otros'
    prioridad = 'baja'

    if any(palabra in texto for palabra in ['agua', 'foco', 'ascensor']):
        categoria = 'mantenimiento'
    if any(palabra in texto for palabra in ['robo', 'sospechoso', 'puerta']):
        categoria = 'seguridad'
        prioridad = 'alta'
    elif any(palabra in texto for palabra in ['limpieza', 'basura']):
        categoria = 'servicios'

    return categoria, prioridad


def build_timeline(incidencia):
    timeline = [
        {
            'estado': 'Reportado',
            'fecha': timezone.localtime(incidencia.fecha_creacion).strftime('%Y-%m-%d %H:%M'),
        }
    ]
    seguimientos = IncidenciaSeguimiento.objects.filter(id_incidencia=incidencia).order_by('fecha_registro')
    for seguimiento in seguimientos:
        timeline.append({
            'estado': seguimiento.comentario or seguimiento.estado_nuevo,
            'fecha': timezone.localtime(seguimiento.fecha_registro).strftime('%Y-%m-%d %H:%M'),
        })
    return timeline


def serialize_incidencia(incidencia):
    return {
        'id': incidencia.id,
        'residente_id': incidencia.id_residente.id_usuario_id,
        'titulo': incidencia.titulo,
        'descripcion': incidencia.descripcion,
        'categoria_ia': incidencia.categoria,
        'prioridad_ia': incidencia.prioridad,
        'estado': 'asignada' if incidencia.estado == 'asignado' else incidencia.estado,
        'fecha': timezone.localtime(incidencia.fecha_creacion).date().isoformat(),
        'asignado_a': incidencia.clasificacion_ia,
        'timeline': build_timeline(incidencia),
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def incidencias_view(request):
    if request.method == 'GET':
        residente_id = request.query_params.get('residente_id')
        incidencias = Incidencia.objects.select_related('id_residente__id_usuario').order_by('-fecha_creacion', '-id')
        if residente_id:
            incidencias = incidencias.filter(id_residente__id_usuario_id=residente_id)
        return Response([serialize_incidencia(incidencia) for incidencia in incidencias])

    residente = get_residente_by_user_id(request.data.get('residente_id'))
    if not residente:
        return Response({'error': 'Residente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    categoria, prioridad = clasificar_incidencia(request.data.get('descripcion'))
    incidencia = Incidencia.objects.create(
        id_residente=residente,
        titulo=request.data.get('titulo', ''),
        descripcion=request.data.get('descripcion', ''),
        categoria=categoria,
        prioridad=prioridad,
        estado='nuevo',
        fecha_creacion=timezone.now(),
    )
    return Response(serialize_incidencia(incidencia), status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def asignar_incidencia(request, incidencia_id):
    incidencia = Incidencia.objects.filter(pk=incidencia_id).first()
    if not incidencia:
        return Response({'error': 'Incidencia no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    trabajador = (request.data.get('trabajador') or '').strip()
    incidencia.clasificacion_ia = trabajador
    incidencia.estado = 'asignado'
    incidencia.save(update_fields=['clasificacion_ia', 'estado'])
    IncidenciaSeguimiento.objects.create(
        id_incidencia=incidencia,
        id_usuario=request.user,
        comentario=f'Asignado a {trabajador}',
        estado_anterior='nuevo',
        estado_nuevo='asignado',
        fecha_registro=timezone.now(),
    )
    return Response(serialize_incidencia(incidencia))


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cerrar_incidencia(request, incidencia_id):
    incidencia = Incidencia.objects.filter(pk=incidencia_id).first()
    if not incidencia:
        return Response({'error': 'Incidencia no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    estado_anterior = incidencia.estado
    incidencia.estado = 'cerrado'
    incidencia.fecha_cierre = timezone.now()
    incidencia.save(update_fields=['estado', 'fecha_cierre'])
    IncidenciaSeguimiento.objects.create(
        id_incidencia=incidencia,
        id_usuario=request.user,
        comentario='Cerrada',
        estado_anterior=estado_anterior,
        estado_nuevo='cerrado',
        fecha_registro=timezone.now(),
    )
    return Response(serialize_incidencia(incidencia))
