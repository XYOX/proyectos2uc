from django.db import models


class Comunicacion(models.Model):
    TIPO_CHOICES = [
        ('informativo', 'Informativo'),
        ('urgente', 'Urgente'),
        ('recordatorio', 'Recordatorio'),
    ]

    id_admin_remitente = models.ForeignKey('usuarios.Administrador', on_delete=models.CASCADE, db_column='id_admin_remitente')
    titulo = models.TextField()
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField()
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)

    class Meta:
        db_table = 'Comunicacion'

    def __str__(self):
        return f'{self.titulo} [{self.tipo}]'


class ComunicacionDestinatario(models.Model):
    id_comunicacion = models.ForeignKey(Comunicacion, on_delete=models.CASCADE, db_column='id_comunicacion')
    id_residente = models.ForeignKey('usuarios.Residente', on_delete=models.CASCADE, db_column='id_residente')

    class Meta:
        db_table = 'Comunicacion_Destinatario'

    def __str__(self):
        return f'Comunicacion {self.id_comunicacion_id} -> Residente {self.id_residente_id}'


class Notificacion(models.Model):
    id_residente = models.ForeignKey('usuarios.Residente', on_delete=models.CASCADE, db_column='id_residente')
    id_comunicacion = models.ForeignKey(
        Comunicacion, null=True, blank=True,
        on_delete=models.SET_NULL, db_column='id_comunicacion'
    )
    tipo = models.TextField()
    url_accion = models.TextField(null=True, blank=True)
    leido = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Notificacion'

    def __str__(self):
        return f'Notificacion {self.tipo} - leido={self.leido}'


class Documento(models.Model):
    titulo = models.TextField()
    archivo_url = models.TextField()
    fecha_publicacion = models.DateTimeField()
    id_administrador = models.ForeignKey('usuarios.Administrador', on_delete=models.CASCADE, db_column='id_administrador')

    class Meta:
        db_table = 'Documento'

    def __str__(self):
        return self.titulo
