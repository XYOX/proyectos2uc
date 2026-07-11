from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Administrador, Residente
from .models import CuotaMantenimiento, Pago


def get_residente_by_user_id(user_id):
    return Residente.objects.filter(id_usuario_id=user_id).select_related('id_usuario').first()


def serialize_pago(pago, request=None):
    comprobante_url = None
    if pago.comprobante_url:
        if request:
            comprobante_url = request.build_absolute_uri(pago.comprobante_url.url)
        else:
            comprobante_url = pago.comprobante_url.url
    return {
        'id': pago.id,
        'residente_id': pago.id_residente.id_usuario_id,
        'monto': pago.monto,
        'fecha': pago.fecha_pago.isoformat(),
        'estado': pago.estado,
        'recibo': comprobante_url or (pago.comprobante_url.name if pago.comprobante_url else None),
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pagos_view(request):
    if request.method == 'GET':
        residente_id = request.query_params.get('residente_id')
        pagos = Pago.objects.select_related('id_residente__id_usuario').order_by('-fecha_pago', '-id')
        if residente_id:
            pagos = pagos.filter(id_residente__id_usuario_id=residente_id)
        return Response([serialize_pago(pago, request) for pago in pagos])

    # POST — acepta multipart/form-data (con archivo) o JSON (sin archivo)
    residente_id = request.data.get('residente_id')
    residente = get_residente_by_user_id(residente_id)
    if not residente:
        return Response({'error': 'Residente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    monto = request.data.get('monto')
    if monto is None:
        return Response({'error': 'El monto es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

    cuota, _ = CuotaMantenimiento.objects.get_or_create(
        id_residente=residente,
        periodo=timezone.now().strftime('%Y-%m'),
        defaults={
            'monto': monto,
            'fecha_vencimiento': timezone.localdate(),
            'estado': 'pendiente',
        },
    )

    pago = Pago(
        id_cuota=cuota,
        id_residente=residente,
        monto=monto,
        fecha_pago=timezone.localdate(),
        estado='pendiente',
    )

    archivo = request.FILES.get('comprobante')
    if archivo:
        pago.comprobante_url = archivo

    pago.save()
    return Response(serialize_pago(pago, request), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pagos_pendientes(request):
    pagos = Pago.objects.filter(estado='pendiente').select_related('id_residente__id_usuario').order_by('-fecha_pago', '-id')
    return Response([serialize_pago(pago, request) for pago in pagos])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def validar_pago(request, pago_id):
    pago = Pago.objects.select_related('id_residente', 'id_cuota').filter(pk=pago_id).first()
    if not pago:
        return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    aprobar = bool(request.data.get('aprobar'))
    pago.estado = 'aprobado' if aprobar else 'rechazado'
    pago.fecha_validacion = timezone.now()

    admin = Administrador.objects.filter(id_usuario=request.user).first()
    if admin:
        pago.id_admin_validador = admin

    if aprobar:
        pago.id_residente.estado_financiero = 'al_dia'
        pago.id_residente.save(update_fields=['estado_financiero'])
        pago.id_cuota.estado = 'pagado'
        pago.id_cuota.save(update_fields=['estado'])

    pago.save(update_fields=['estado', 'fecha_validacion', 'id_admin_validador'])
    return Response(serialize_pago(pago, request))
