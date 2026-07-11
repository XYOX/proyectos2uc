from django.db import models


class AreaComun(models.Model):
    nombre = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    capacidad = models.IntegerField()
    horario_inicio = models.TimeField()
    horario_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'Area_Comun'

    def __str__(self):
        return self.nombre


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    id_residente = models.ForeignKey('usuarios.Residente', on_delete=models.CASCADE, db_column='id_residente')
    id_area = models.ForeignKey(AreaComun, on_delete=models.CASCADE, db_column='id_area')
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    fecha_solicitud = models.DateTimeField()

    class Meta:
        db_table = 'Reserva'

    def __str__(self):
        return f'Reserva {self.id_area} - {self.fecha_reserva}'
