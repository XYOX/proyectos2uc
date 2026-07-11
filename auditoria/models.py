from django.db import models


class LogAuditoria(models.Model):
    id_usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, db_column='id_usuario')
    accion = models.TextField()
    entidad_afectada = models.TextField()
    id_registro_afectado = models.IntegerField()
    fecha_hora = models.DateTimeField()
    ip_origen = models.TextField(null=True, blank=True)
    navegador = models.TextField(null=True, blank=True)
    detalle = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Log_Auditoria'

    def __str__(self):
        return f'Log {self.accion} - {self.fecha_hora}'
