from django.db              import models
from django.core.exceptions import ValidationError
from django.utils           import timezone
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
    
    class Meta:
        db_table            = 'solicitud'
        verbose_name        = 'Solicitud'
        verbose_name_plural = 'Solicitudes'
        ordering            = ['-fecha_solicitud']

    def clean(self):
        # fecha_solicitud tiene auto_now_add — en objetos nuevos es None durante clean()
        # usamos today como referencia segura
        today = timezone.now().date()

        if self.fecha_llegada and self.fecha_llegada < today:
            raise ValidationError('La fecha de llegada no puede ser anterior a hoy.')
        if self.fecha_llegada and self.fecha_salida and self.fecha_salida <= self.fecha_llegada:
            raise ValidationError('La fecha de salida debe ser posterior a la de llegada.')

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
        es_nuevo        = self.pk is None

        if not es_nuevo:
            anterior        = Solicitud.objects.get(pk=self.pk)
            estado_anterior = anterior.estado

        super().save(*args, **kwargs)

         # SolicitudHistorial está en el mismo archivo — sin import
        if es_nuevo:
            SolicitudHistorial.objects.create(
                solicitud=self,
                estado_anterior=None,
                estado_nuevo=self.estado,
            )
        elif estado_anterior != self.estado:
            SolicitudHistorial.objects.create(
                solicitud=self,
                estado_anterior=estado_anterior,
                estado_nuevo=self.estado,
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
        db_table            = 'solicitud_historial'
        verbose_name        = 'Historial de solicitud'
        verbose_name_plural = 'Historial de solicitudes'
        ordering            = ['-fecha_cambio']

    def __str__(self):
        return f"Solicitud {self.solicitud.id}: {self.estado_anterior} -> {self.estado_nuevo}"