from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.solicitudes.models import Solicitud
from apps.muelles.models import Muelle


class Asignacion(models.Model):
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="asignaciones"
    )
    muelle = models.ForeignKey(
        Muelle,
        on_delete=models.PROTECT,
        related_name="asignaciones"
    )
    administrador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="asignaciones"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    pos_inicio = models.IntegerField()
    pos_fin = models.IntegerField()

    class Meta:
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"

    def clean(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha fin debe ser posterior a la fecha inicio.")

        if self.pos_fin < self.pos_inicio:
            raise ValidationError("La posición final no puede ser menor que la posición inicial.")

        if not self.muelle.estado:
            raise ValidationError("No se puede asignar: el muelle está inactivo.")

        if self.fecha_inicio < self.solicitud.fecha_llegada:
            raise ValidationError("La fecha de inicio no puede ser anterior a la llegada de la solicitud.")

        if self.fecha_fin > self.solicitud.fecha_salida:
            raise ValidationError("La fecha fin no puede ser posterior a la salida de la solicitud.")

        traslapes = Asignacion.objects.filter(
            muelle=self.muelle,
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio
        )

        if self.pk:
            traslapes = traslapes.exclude(pk=self.pk)

        if traslapes.exists():
            raise ValidationError("Ese muelle ya tiene una asignación en esas fechas.")

    def __str__(self):
        return f"{self.solicitud.embarcacion.nombre_bote} -> {self.muelle.nombre}"