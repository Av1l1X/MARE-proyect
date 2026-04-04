from django.contrib import admin
from apps.solicitudes.models import Solicitud, SolicitudHistorial

admin.site.register(Solicitud)
admin.site.register(SolicitudHistorial)