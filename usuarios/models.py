from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'administrador')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('residente', 'Residente'),
        ('administrador', 'Administrador'),
    ]
    NACIONALIDAD_CHOICES = [
        ('peruana', 'Peruana'),
        ('extranjero', 'Extranjero'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('Carnet de Extranjería', 'Carnet de Extranjería'),
    ]

    nombres = models.TextField()
    apellidos = models.TextField()
    nombre = models.TextField()
    email = models.EmailField(unique=True)
    telefono = models.TextField(null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    nacionalidad = models.CharField(max_length=20, choices=NACIONALIDAD_CHOICES, default='peruana')
    tipo_documento = models.CharField(max_length=30, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.TextField(unique=True)
    fecha_nacimiento = models.DateField()
    # is_active reemplaza a 'activo'; is_staff permite acceso al admin de Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombres', 'apellidos', 'nombre', 'rol', 'tipo_documento', 'numero_documento', 'fecha_nacimiento']

    objects = UsuarioManager()

    class Meta:
        db_table = 'Usuario'

    def __str__(self):
        return f'{self.nombre} ({self.email})'


class Residente(models.Model):
    ESTADO_FINANCIERO_CHOICES = [
        ('al_dia', 'Al día'),
        ('moroso', 'Moroso'),
    ]

    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    nro_departamento = models.TextField()
    estado_financiero = models.CharField(max_length=10, choices=ESTADO_FINANCIERO_CHOICES)
    fecha_ingreso = models.DateField()

    class Meta:
        db_table = 'Residente'

    def __str__(self):
        return f'Residente {self.nro_departamento} - {self.id_usuario}'


class Administrador(models.Model):
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    cargo = models.TextField()
    permisos = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Administrador'

    def __str__(self):
        return f'Admin: {self.cargo} - {self.id_usuario}'


class Invitacion(models.Model):
    codigo = models.TextField(unique=True)
    dpto_destino = models.TextField()
    usado = models.BooleanField(default=False)
    id_admin_creador = models.ForeignKey(Administrador, on_delete=models.CASCADE, db_column='id_admin_creador')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Invitacion'

    def __str__(self):
        return f'Invitacion {self.codigo} -> {self.dpto_destino}'


class SolicitudRegistro(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    nombres = models.TextField()
    apellidos = models.TextField()
    email = models.EmailField()
    telefono = models.TextField(null=True, blank=True)
    dpto_solicitado = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    motivo_rechazo = models.TextField(null=True, blank=True)
    id_admin_procesa = models.ForeignKey(
        Administrador, null=True, blank=True,
        on_delete=models.SET_NULL, db_column='id_admin_procesa'
    )

    class Meta:
        db_table = 'Solicitud_Registro'

    def __str__(self):
        return f'Solicitud {self.email} [{self.estado}]'
