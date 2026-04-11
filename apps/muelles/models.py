from django.db import models
from django.core.exceptions import ValidationError


class Muelle(models.Model):
    nombre = models.CharField(max_length=120)
    tam_maximo = models.DecimalField(max_digits=6, decimal_places=2)
    total_espacios = models.PositiveIntegerField(default=0)  # ← para el mapa SVG


    estado = models.BooleanField(default=True)
    coordenada_x = models.DecimalField(max_digits=10, decimal_places=6)
    coordenada_y = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta:
        db_table            = 'muelle'

        verbose_name        = 'Muelle'
        verbose_name_plural = 'Muelles'
        ordering            = ['nombre']


    def clean(self):
        if self.tam_maximo is not None and self.tam_maximo <= 0:
            raise ValidationError('El tamaño máximo debe ser mayor a 0.')
        if self.total_espacios is not None and self.total_espacios < 1:
            raise ValidationError('El muelle debe tener al menos 1 espacio.')

    def __str__(self):
        return self.nombre


class Espacio(models.Model):
    muelle     = models.ForeignKey(
        Muelle,
        on_delete=models.CASCADE,       # si se borra el muelle, se borran sus espacios
        related_name='espacios'
    )
    numero     = models.PositiveIntegerField()
    pos_x      = models.DecimalField(max_digits=8, decimal_places=2)  # coord X en el canvas SVG
    pos_y      = models.DecimalField(max_digits=8, decimal_places=2)  # coord Y en el canvas SVG
    ancho      = models.DecimalField(max_digits=6, decimal_places=2)  # width del rectángulo
    alto       = models.DecimalField(max_digits=6, decimal_places=2)  # height del rectángulo
    es_pasillo = models.BooleanField(default=False)                   # pasillo visual, no asignable
    activo     = models.BooleanField(default=True)

    class Meta:
        db_table            = 'espacio'
        verbose_name        = 'Espacio'
        verbose_name_plural = 'Espacios'
        ordering            = ['muelle', 'numero']
        # No puede haber dos espacios con el mismo número en el mismo muelle
        constraints = [
            models.UniqueConstraint(
                fields=['muelle', 'numero'],
                name='uq_espacio_muelle_numero'
            )
        ]

    def clean(self):
        if self.ancho is not None and self.ancho <= 0:
            raise ValidationError('El ancho debe ser mayor a 0.')
        if self.alto is not None and self.alto <= 0:
            raise ValidationError('El alto debe ser mayor a 0.')

    def __str__(self):
        return f'{self.muelle.nombre} — Espacio {self.numero}'