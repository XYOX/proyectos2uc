from django.db import models


class Incidencia(models.Model):
    CATEGORIA_CHOICES = [
        ("mantenimiento", "Mantenimiento"),
        ("seguridad", "Seguridad"),
        ("servicios", "Servicios"),
        ("otros", "Otros"),
    ]
    PRIORIDAD_CHOICES = [
        ("baja", "Baja"),
        ("media", "Media"),
        ("alta", "Alta"),
    ]
    ESTADO_CHOICES = [
        ("nuevo", "Nuevo"),
        ("asignado", "Asignado"),
        ("en_progreso", "En Progreso"),
        ("resuelto", "Resuelto"),
        ("cerrado", "Cerrado"),
    ]

    id_residente = models.ForeignKey(
        "usuarios.Residente", on_delete=models.CASCADE, db_column="id_residente"
    )
    titulo = models.TextField()
    descripcion = models.TextField()
    categoria = models.CharField(max_length=15, choices=CATEGORIA_CHOICES)
    prioridad = models.CharField(max_length=5, choices=PRIORIDAD_CHOICES)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES)
    fecha_creacion = models.DateTimeField()
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    evidencia_url = models.TextField(null=True, blank=True)
    id_admin_asignado = models.ForeignKey(
        "usuarios.Administrador",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="id_admin_asignado",
    )
    clasificacion_ia = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "Incidencia"

    def __str__(self):
        return f"{self.titulo} [{self.estado}]"


class IncidenciaSeguimiento(models.Model):
    id_incidencia = models.ForeignKey(
        Incidencia, on_delete=models.CASCADE, db_column="id_incidencia"
    )
    id_usuario = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.CASCADE, db_column="id_usuario"
    )
    comentario = models.TextField()
    estado_anterior = models.TextField()
    estado_nuevo = models.TextField()
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = "Incidencia_Seguimiento"

    def __str__(self):
        return f"Seguimiento incidencia {self.id_incidencia_id}"
