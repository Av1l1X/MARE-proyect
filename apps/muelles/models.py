from django.db import models
from django.core.exceptions import ValidationError


class Muelle(models.Model):
    nombre = models.CharField(max_length=120)
    tam_maximo = models.DecimalField(max_digits=6, decimal_places=2)
    estado = models.BooleanField(default=True)
    coordenada_x = models.DecimalField(max_digits=10, decimal_places=6)
    coordenada_y = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta:
        verbose_name = "Muelle"
        verbose_name_plural = "Muelles"

    def clean(self):
        if self.tam_maximo <= 0:
            raise ValidationError("El tamaño máximo debe ser mayor a 0.")

    def __str__(self):
        return self.nombre
