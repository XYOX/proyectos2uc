from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Administrador
from .models import Comunicacion


def serialize_anuncio(anuncio):
    return {
        'id': anuncio.id,
        'titulo': anuncio.titulo,
        'mensaje': anuncio.mensaje,
        'fecha': timezone.localtime(anuncio.fecha_envio).strftime('%Y-%m-%d %H:%M'),
        'autor': anuncio.id_admin_remitente.id_usuario.nombre,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def anuncios_view(request):
    if request.method == 'GET':
        anuncios = Comunicacion.objects.select_related('id_admin_remitente__id_usuario').order_by('-fecha_envio', '-id')
        return Response([serialize_anuncio(anuncio) for anuncio in anuncios])

    admin = Administrador.objects.filter(id_usuario=request.user).select_related('id_usuario').first()
    if not admin:
        return Response({'error': 'Solo los administradores pueden publicar anuncios.'}, status=status.HTTP_403_FORBIDDEN)

    anuncio = Comunicacion.objects.create(
        id_admin_remitente=admin,
        titulo=request.data.get('titulo', ''),
        mensaje=request.data.get('mensaje', ''),
        fecha_envio=timezone.now(),
        tipo='informativo',
    )
    return Response(serialize_anuncio(anuncio), status=status.HTTP_201_CREATED)
