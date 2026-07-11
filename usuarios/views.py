from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Invitacion, Residente, SolicitudRegistro, Usuario


def serialize_current_user(user):
    try:
        residente = user.residente
    except Residente.DoesNotExist:
        residente = None
    return {
        'id': user.id,
        'nombre': user.nombre,
        'email': user.email,
        'rol': user.rol,
        'dpto': residente.nro_departamento if residente else None,
        'estado_financiero': residente.estado_financiero if residente else None,
        'deuda': 0,
        'activo': user.is_active,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    return Response(serialize_current_user(request.user))


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def registro_usuario(request):
    data = request.data
    email = (data.get('email') or '').strip().lower()
    codigo = (data.get('codigo') or '').strip().upper()
    dpto = (data.get('dpto') or '').strip()

    if Usuario.objects.filter(email=email).exists():
        return Response({'error': 'El correo ya está registrado.'}, status=status.HTTP_400_BAD_REQUEST)

    if not codigo and not dpto:
        return Response({'error': 'Debes ingresar un departamento o un código de invitación.'}, status=status.HTTP_400_BAD_REQUEST)

    nombre_completo = f"{(data.get('nombres') or '').strip()} {(data.get('apellidos') or '').strip()}".strip()
    activo = False
    residente = None

    user = Usuario.objects.create_user(
        email=email,
        password=data.get('password'),
        nombres=(data.get('nombres') or '').strip(),
        apellidos=(data.get('apellidos') or '').strip(),
        nombre=nombre_completo,
        telefono=(data.get('telefono') or '').strip(),
        rol='residente',
        nacionalidad=data.get('nacionalidad') or 'peruana',
        tipo_documento=data.get('tipo_documento') or 'DNI',
        numero_documento=(data.get('numero_documento') or '').strip(),
        fecha_nacimiento=data.get('fecha_nacimiento'),
        is_active=False,
    )

    if codigo:
        invitacion = Invitacion.objects.filter(codigo=codigo, usado=False).select_related('id_admin_creador').first()
        if not invitacion:
            transaction.set_rollback(True)
            return Response({'error': 'Código de invitación inválido o ya usado.'}, status=status.HTTP_400_BAD_REQUEST)

        invitacion.usado = True
        invitacion.save(update_fields=['usado'])
        user.is_active = True
        user.save(update_fields=['is_active'])
        residente = Residente.objects.create(
            id_usuario=user,
            nro_departamento=invitacion.dpto_destino,
            estado_financiero='al_dia',
            fecha_ingreso=timezone.localdate(),
        )
        activo = True

    else:
        SolicitudRegistro.objects.create(
            nombres=user.nombres,
            apellidos=user.apellidos,
            email=user.email,
            telefono=user.telefono,
            dpto_solicitado=dpto,
        )

    if activo and residente:
        return Response({'mensaje': 'Registro exitoso. Ya puedes iniciar sesión.'}, status=status.HTTP_201_CREATED)

    return Response({'mensaje': 'Registro exitoso. Tu cuenta está pendiente de aprobación por el administrador.'}, status=status.HTTP_201_CREATED)
