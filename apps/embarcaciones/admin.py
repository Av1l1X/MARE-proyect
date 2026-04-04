from django.contrib import admin
from apps.embarcaciones.models import TipoBarco, Embarcacion

admin.site.register(TipoBarco)
admin.site.register(Embarcacion)