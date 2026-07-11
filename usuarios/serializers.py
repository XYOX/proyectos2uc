from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Residente


class CondoTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        try:
            residente = user.residente
        except Residente.DoesNotExist:
            residente = None
        data['user'] = {
            'id': user.id,
            'nombre': user.nombre,
            'email': user.email,
            'rol': user.rol,
            'dpto': residente.nro_departamento if residente else None,
            'estado_financiero': residente.estado_financiero if residente else None,
            'deuda': 0,
            'activo': user.is_active,
        }
        return data


class CondoTokenObtainPairView(TokenObtainPairView):
    serializer_class = CondoTokenObtainPairSerializer
