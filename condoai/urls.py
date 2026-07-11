from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from usuarios.serializers import CondoTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', CondoTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('api.urls')),
    path('api/', include('usuarios.urls')),
    path('api/', include('pagos.urls')),
    path('api/', include('incidencias.urls')),
    path('api/', include('reservas.urls')),
    path('api/', include('comunicaciones.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
