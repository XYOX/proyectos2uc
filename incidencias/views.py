from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Residente
from .models import Incidencia, IncidenciaSeguimiento


def get_residente_by_user_id(user_id):
    return (
        Residente.objects.filter(id_usuario_id=user_id)
        .select_related("id_usuario")
        .first()
    )


def clasificar_incidencia(titulo, descripcion):
    """
    Clasifica automáticamente la incidencia usando Gemini 2.5 Flash en modo JSON nativo.
    Sigue lineamientos ITIL 4 para priorización.
    Retorna (categoria, prioridad, razon_ia).
    """
    import json
    from google import genai
    from google.genai import types

    api_key = getattr(settings, "GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY no está configurada en el servidor.")

    instrucciones_sistema = """Eres un sistema experto en gestión de incidencias para condominios, siguiendo el marco ITIL 4.
Responde estrictamente con un objeto JSON usando estas claves: "categoria", "prioridad" y "razon".

Criterios ITIL 4 de priorización:
- Alta: impacta seguridad física, servicios esenciales (agua, electricidad), o afecta a múltiples residentes.
- Media: afecta comodidad o funcionamiento normal, resolución en 48h.
- Baja: cosmético, informativo, o sin urgencia.

Categorías válidas: mantenimiento, seguridad, servicios, otros.
Prioridades válidas: baja, media, alta."""

    texto_completo = f"Título: {titulo}\nDescripción: {descripcion}"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=texto_completo,
            config=types.GenerateContentConfig(
                system_instruction=instrucciones_sistema,
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
        categoria = data.get("categoria", "otros")
        prioridad = data.get("prioridad", "baja")
        razon = data.get("razon", "")
        if categoria not in ["mantenimiento", "seguridad", "servicios", "otros"]:
            categoria = "otros"
        if prioridad not in ["baja", "media", "alta"]:
            prioridad = "baja"
        return categoria, prioridad, razon
    except Exception as e:
        raise ValueError(f"Error al conectar con Gemini: {e}")


def build_timeline(incidencia):
    timeline = [
        {
            "estado": "Reportado",
            "fecha": timezone.localtime(incidencia.fecha_creacion).strftime(
                "%Y-%m-%d %H:%M"
            ),
        }
    ]
    seguimientos = IncidenciaSeguimiento.objects.filter(
        id_incidencia=incidencia
    ).order_by("fecha_registro")
    for seguimiento in seguimientos:
        timeline.append(
            {
                "estado": seguimiento.comentario or seguimiento.estado_nuevo,
                "fecha": timezone.localtime(seguimiento.fecha_registro).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
        )
    return timeline


def serialize_incidencia(incidencia, request=None):
    evidencia_url = None
    if incidencia.evidencia and incidencia.evidencia.name:
        evidencia_url = (
            request.build_absolute_uri(incidencia.evidencia.url)
            if request
            else incidencia.evidencia.url
        )
    return {
        "id": incidencia.id,
        "residente_id": incidencia.id_residente.id_usuario_id,
        "titulo": incidencia.titulo,
        "descripcion": incidencia.descripcion,
        "categoria_ia": incidencia.categoria,
        "prioridad_ia": incidencia.prioridad,
        "estado": "asignada" if incidencia.estado == "asignado" else incidencia.estado,
        "fecha": timezone.localtime(incidencia.fecha_creacion).date().isoformat(),
        "asignado_a": incidencia.clasificacion_ia,
        "evidencia_url": evidencia_url,
        "timeline": build_timeline(incidencia),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def incidencias_view(request):
    if request.method == "GET":
        residente_id = request.query_params.get("residente_id")
        incidencias = Incidencia.objects.select_related(
            "id_residente__id_usuario"
        ).order_by("-fecha_creacion", "-id")
        if residente_id:
            incidencias = incidencias.filter(id_residente__id_usuario_id=residente_id)
        return Response(
            [serialize_incidencia(incidencia, request) for incidencia in incidencias]
        )

    residente = get_residente_by_user_id(request.data.get("residente_id"))
    if not residente:
        return Response(
            {"error": "Residente no encontrado."}, status=status.HTTP_404_NOT_FOUND
        )

    # Validar evidencia (máx 5MB, formatos permitidos)
    evidencia = request.FILES.get("evidencia")
    if evidencia:
        if evidencia.size > 5 * 1024 * 1024:
            return Response(
                {"error": "El archivo no debe superar los 5MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ext = evidencia.name.rsplit(".", 1)[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "pdf"]:
            return Response(
                {"error": "Solo se permiten archivos JPG, PNG o PDF."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    titulo = request.data.get("titulo", "")
    descripcion = request.data.get("descripcion", "")
    try:
        categoria, prioridad, razon_ia = clasificar_incidencia(titulo, descripcion)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    incidencia = Incidencia.objects.create(
        id_residente=residente,
        titulo=titulo,
        descripcion=descripcion,
        categoria=categoria,
        prioridad=prioridad,
        estado="nuevo",
        fecha_creacion=timezone.now(),
        clasificacion_ia=razon_ia,
        evidencia=evidencia,
    )
    return Response(
        serialize_incidencia(incidencia, request), status=status.HTTP_201_CREATED
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def asignar_incidencia(request, incidencia_id):
    incidencia = Incidencia.objects.filter(pk=incidencia_id).first()
    if not incidencia:
        return Response(
            {"error": "Incidencia no encontrada."}, status=status.HTTP_404_NOT_FOUND
        )

    trabajador = (request.data.get("trabajador") or "").strip()
    incidencia.clasificacion_ia = trabajador
    incidencia.estado = "asignado"
    incidencia.save(update_fields=["clasificacion_ia", "estado"])
    IncidenciaSeguimiento.objects.create(
        id_incidencia=incidencia,
        id_usuario=request.user,
        comentario=f"Asignado a {trabajador}",
        estado_anterior="nuevo",
        estado_nuevo="asignado",
        fecha_registro=timezone.now(),
    )
    return Response(serialize_incidencia(incidencia, request))


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def cerrar_incidencia(request, incidencia_id):
    incidencia = Incidencia.objects.filter(pk=incidencia_id).first()
    if not incidencia:
        return Response(
            {"error": "Incidencia no encontrada."}, status=status.HTTP_404_NOT_FOUND
        )

    estado_anterior = incidencia.estado
    incidencia.estado = "cerrado"
    incidencia.fecha_cierre = timezone.now()
    incidencia.save(update_fields=["estado", "fecha_cierre"])
    IncidenciaSeguimiento.objects.create(
        id_incidencia=incidencia,
        id_usuario=request.user,
        comentario="Cerrada",
        estado_anterior=estado_anterior,
        estado_nuevo="cerrado",
        fecha_registro=timezone.now(),
    )
    return Response(serialize_incidencia(incidencia, request))
