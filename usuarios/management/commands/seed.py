from datetime import date, time

from django.core.management.base import BaseCommand

from reservas.models import AreaComun
from usuarios.models import Administrador, Residente, Usuario


class Command(BaseCommand):
    help = 'Carga datos de prueba para CondoAI.'

    def handle(self, *args, **options):
        residente_1, _ = Usuario.objects.get_or_create(
            email='bhuaman@condo.pe',
            defaults={
                'nombres': 'Bryans',
                'apellidos': 'Huaman',
                'nombre': 'Bryans Huaman',
                'telefono': '999111222',
                'rol': 'residente',
                'nacionalidad': 'peruana',
                'tipo_documento': 'DNI',
                'numero_documento': '70000001',
                'fecha_nacimiento': date(1995, 1, 15),
                'is_active': True,
            },
        )
        residente_1.set_password('123')
        residente_1.is_active = True
        residente_1.rol = 'residente'
        residente_1.nombre = 'Bryans Huaman'
        residente_1.nombres = 'Bryans'
        residente_1.apellidos = 'Huaman'
        residente_1.save()
        Residente.objects.update_or_create(
            id_usuario=residente_1,
            defaults={
                'nro_departamento': '101',
                'estado_financiero': 'al_dia',
                'fecha_ingreso': date.today(),
            },
        )

        residente_2, _ = Usuario.objects.get_or_create(
            email='imacuri@condo.pe',
            defaults={
                'nombres': 'Iván',
                'apellidos': 'Macuri',
                'nombre': 'Iván Macuri',
                'telefono': '999333444',
                'rol': 'residente',
                'nacionalidad': 'peruana',
                'tipo_documento': 'DNI',
                'numero_documento': '70000002',
                'fecha_nacimiento': date(1992, 6, 20),
                'is_active': True,
            },
        )
        residente_2.set_password('123')
        residente_2.is_active = True
        residente_2.rol = 'residente'
        residente_2.nombre = 'Iván Macuri'
        residente_2.nombres = 'Iván'
        residente_2.apellidos = 'Macuri'
        residente_2.save()
        Residente.objects.update_or_create(
            id_usuario=residente_2,
            defaults={
                'nro_departamento': '202',
                'estado_financiero': 'moroso',
                'fecha_ingreso': date.today(),
            },
        )

        admin_user, _ = Usuario.objects.get_or_create(
            email='admin@condo.pe',
            defaults={
                'nombres': 'Admin',
                'apellidos': 'Condo',
                'nombre': 'Admin Condo',
                'telefono': '999555666',
                'rol': 'administrador',
                'nacionalidad': 'peruana',
                'tipo_documento': 'DNI',
                'numero_documento': '70000003',
                'fecha_nacimiento': date(1988, 3, 10),
                'is_active': True,
                'is_staff': True,
            },
        )
        admin_user.set_password('admin')
        admin_user.is_active = True
        admin_user.is_staff = True
        admin_user.rol = 'administrador'
        admin_user.nombre = 'Admin Condo'
        admin_user.nombres = 'Admin'
        admin_user.apellidos = 'Condo'
        admin_user.save()
        Administrador.objects.update_or_create(
            id_usuario=admin_user,
            defaults={
                'cargo': 'Administrador General',
                'permisos': 'total',
            },
        )

        for nombre in ['Salón Comunal', 'Piscina', 'Gimnasio', 'Cancha de Tenis']:
            AreaComun.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': f'Área común {nombre}',
                    'capacidad': 20,
                    'horario_inicio': time(8, 0),
                    'horario_fin': time(22, 0),
                    'activo': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Datos semilla creados/actualizados correctamente.'))
