"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from apps.mapa import views as mapa_views

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Área pública (cliente)
    path('', include('apps.publico.urls')),

    # Dashboard admin
    path('inicio/', mapa_views.inicio, name='inicio'),

    # Apps
    path('solicitudes/',   include('apps.solicitudes.urls')),
    path('muelles/',       include('apps.muelles.urls')),
    path('mapa/',          include('apps.mapa.urls')),
    path('asignaciones/',  include('apps.asignaciones.urls')),
    path('clientes/',      include('apps.clientes.urls')),
    path('embarcaciones/', include('apps.embarcaciones.urls')),
]
