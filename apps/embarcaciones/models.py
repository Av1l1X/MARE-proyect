from django.db import models
from django.core.exceptions import ValidationError
from apps.clientes.models import Cliente


class TipoBarco(models.Model):
    tipo_barco = models.CharField(max_length=80)

    class Meta:
        verbose_name = "Tipo de barco"
        verbose_name_plural = "Tipos de barco"

    def __str__(self):
        return self.tipo_barco


class Embarcacion(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="embarcaciones"
    )
    tipo_barco = models.ForeignKey(
        TipoBarco,
        on_delete=models.PROTECT,
        related_name="embarcaciones"
    )
    nombre_bote = models.CharField(max_length=50)
    eslora = models.DecimalField(max_digits=6, decimal_places=2)
    manga = models.DecimalField(max_digits=6, decimal_places=2)
    calado = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = "Embarcación"
        verbose_name_plural = "Embarcaciones"

    def clean(self):
        if self.eslora <= 0:
            raise ValidationError("La eslora debe ser mayor a 0.")
        if self.manga <= 0:
            raise ValidationError("La manga debe ser mayor a 0.")
        if self.calado <= 0:
            raise ValidationError("El calado debe ser mayor a 0.")

    def __str__(self):
        return self.nombre_bote