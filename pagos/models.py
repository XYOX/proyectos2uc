from django.db import models


class CuotaMantenimiento(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ]

    id_residente = models.ForeignKey('usuarios.Residente', on_delete=models.CASCADE, db_column='id_residente')
    periodo = models.TextField()
    monto = models.FloatField()
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)

    class Meta:
        db_table = 'Cuota_Mantenimiento'

    def __str__(self):
        return f'Cuota {self.periodo} - {self.estado}'


class Pago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    id_cuota = models.ForeignKey(CuotaMantenimiento, on_delete=models.CASCADE, db_column='id_cuota')
    id_residente = models.ForeignKey('usuarios.Residente', on_delete=models.CASCADE, db_column='id_residente')
    monto = models.FloatField()
    fecha_pago = models.DateField()
    numero_operacion = models.TextField(null=True, blank=True)
    comprobante_url = models.FileField(upload_to='comprobantes/', null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    observacion_validacion = models.TextField(null=True, blank=True)
    id_admin_validador = models.ForeignKey(
        'usuarios.Administrador', null=True, blank=True,
        on_delete=models.SET_NULL, db_column='id_admin_validador'
    )

    class Meta:
        db_table = 'Pago'

    def __str__(self):
        return f'Pago {self.id} - {self.estado}'
