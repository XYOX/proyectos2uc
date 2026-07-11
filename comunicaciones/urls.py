from django.urls import path

from .views import anuncios_view

urlpatterns = [
    path('anuncios/', anuncios_view, name='anuncios'),
]
