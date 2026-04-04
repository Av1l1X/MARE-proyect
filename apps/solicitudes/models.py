from django.db import models
from django.core.exceptions import ValidationError
from apps.embarcaciones.models import Embarcacion


class Solicitud(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("ACTIVA", "Activa"),
        ("COMPLETADA", "Completada"),
        ("CANCELADA", "Cancelada"),
    ]

    embarcacion = models.ForeignKey(
        Embarcacion,
        on_delete=models.PROTECT,
        related_name="solicitudes"
    )
    fecha_solicitud = models.DateField(auto_now_add=True)
    fecha_llegada = models.DateField()
    fecha_salida = models.DateField()
    comentario = models.CharField(max_length=200, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")

    def clean(self):
        if self.fecha_llegada < self.fecha_solicitud:
            raise ValidationError("La fecha de llegada no puede ser anterior a la fecha de solicitud.")
        if self.fecha_salida <= self.fecha_llegada:
            raise ValidationError("La fecha de salida debe ser posterior a la fecha de llegada.")

        if self.pk:
            anterior = Solicitud.objects.get(pk=self.pk)

            if anterior.estado != self.estado:
                if anterior.estado in ["COMPLETADA", "CANCELADA"]:
                    raise ValidationError("Una solicitud completada o cancelada no puede cambiar de estado.")

                if anterior.estado == "PENDIENTE" and self.estado not in ["ACTIVA", "CANCELADA"]:
                    raise ValidationError("Una solicitud pendiente solo puede pasar a activa o cancelada.")

                if anterior.estado == "ACTIVA" and self.estado not in ["COMPLETADA", "CANCELADA"]:
                    raise ValidationError("Una solicitud activa solo puede pasar a completada o cancelada.")

    def save(self, *args, **kwargs):
        estado_anterior = None

        if self.pk:
            anterior = Solicitud.objects.get(pk=self.pk)
            estado_anterior = anterior.estado

        es_nuevo = self.pk is None

        super().save(*args, **kwargs)

        from .models import SolicitudHistorial

        if es_nuevo:
            SolicitudHistorial.objects.create(
                solicitud=self,
                estado_anterior=None,
                estado_nuevo=self.estado
            )
        elif estado_anterior != self.estado:
            SolicitudHistorial.objects.create(
                solicitud=self,
                estado_anterior=estado_anterior,
                estado_nuevo=self.estado
            )

    def __str__(self):
        return f"Solicitud #{self.id} - {self.embarcacion.nombre_bote}"

class SolicitudHistorial(models.Model):
    solicitud = models.ForeignKey(
        "Solicitud",
        on_delete=models.CASCADE,
        related_name="historial"
    )
    estado_anterior = models.CharField(max_length=50, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=50)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de solicitud"
        verbose_name_plural = "Historial de solicitudes"

    def __str__(self):
        return f"Solicitud {self.solicitud.id}: {self.estado_anterior} -> {self.estado_nuevo}"