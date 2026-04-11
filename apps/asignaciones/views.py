from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from apps.solicitudes.models import Solicitud
from apps.muelles.models import Muelle
from .models import Asignacion, Administrador


ASIGNACION_SELECT = (
    'solicitud',
    'solicitud__embarcacion',
    'solicitud__embarcacion__cliente',
    'muelle',
    'administrador__user',
)  # reutilizando en list, detail y update

@login_required
def asignacion_list(request):
    asignaciones = Asignacion.objects.select_related(
        *ASIGNACION_SELECT
    ).order_by("-fecha_inicio", "-id")

    paginator = Paginator(asignaciones, 10)
    numero_pagina = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(numero_pagina)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        "page_obj": page_obj,
        "asignaciones": page_obj.object_list,
    }
    
    return render(request, "asignaciones/asignacion_list.html", context)

@login_required
def asignacion_detail(request, pk):
    asignacion = get_object_or_404(
        Asignacion.objects.select_related(
            *ASIGNACION_SELECT
        ),
        pk=pk
    )

    return render(request, "asignaciones/asignacion_detail.html", {
        "asignacion": asignacion
    })

@login_required
def asignacion_create(request):
      # El usuario logueado debe tener perfil Administrador
    administrador = get_object_or_404(Administrador, user=request.user)
    
    solicitudes = Solicitud.objects.select_related(
        "embarcacion__cliente"
    ).exclude(
        estado__in=["COMPLETADA", "CANCELADA"]
    ).order_by("-fecha_solicitud")

    muelles = Muelle.objects.filter(estado=True).order_by("nombre")

    context = {
        "solicitudes": solicitudes,
        "muelles": muelles,
    }

    if request.method == "POST":
        asignacion = Asignacion(
        solicitud_id = request.POST.get("solicitud"),
        muelle_id = request.POST.get("muelle"),
        administrador = administrador,
        
        fecha_inicio = request.POST.get("fecha_inicio"),
        fecha_fin = request.POST.get("fecha_fin"),
        pos_inicio = request.POST.get("pos_inicio"),
        pos_fin = request.POST.get("pos_fin"),

        )

        try:
            asignacion.full_clean()
            asignacion.save()
            messages.success(request, "Asignación creada correctamente.")
            return redirect("asignacion_list")
        except ValidationError as exc:
            context["errors"] = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            context["asignacion"] = asignacion

    return render(request, "asignaciones/asignacion_form.html", context)

@login_required
def asignacion_update(request, pk):
    asignacion = get_object_or_404(Asignacion, pk=pk)

    solicitudes = Solicitud.objects.select_related(
        "embarcacion__cliente"
    ).exclude(
        estado__in=["COMPLETADA", "CANCELADA"]
    ).order_by("-fecha_solicitud")

    muelles = Muelle.objects.filter(estado=True).order_by("nombre")

    context = {
        "asignacion": asignacion,
        "solicitudes": solicitudes,
        "muelles": muelles,
    }

    if request.method == "POST":
        asignacion.solicitud_id = request.POST.get("solicitud")
        asignacion.muelle_id = request.POST.get("muelle")
        asignacion.fecha_inicio = request.POST.get("fecha_inicio")
        asignacion.fecha_fin = request.POST.get("fecha_fin")
        asignacion.pos_inicio = request.POST.get("pos_inicio")
        asignacion.pos_fin = request.POST.get("pos_fin")

        try:
            asignacion.full_clean()
            asignacion.save()
            messages.success(request, "Asignación actualizada correctamente.")
            return redirect("asignacion_detail", pk=asignacion.pk)
        except ValidationError as exc:
            context["errors"] = exc.message_dict if hasattr(exc, "message_dict") else exc.messages

    return render(request, "asignaciones/asignacion_form.html", context)

@login_required
def asignacion_delete(request, pk):
    asignacion = get_object_or_404(Asignacion, pk=pk)

    if request.method == "POST":
        solicitud = asignacion.solicitud
        asignacion.delete()

         # Si la solicitud queda sin asignaciones y estaba Activa → regresa a Pendiente
        # Saltamos full_clean() aquí porque esta transición inversa no está en el flujo
        # normal — es una corrección interna del sistema al borrar una asignación
        if not solicitud.asignaciones.exists() and solicitud.estado == 'ACTIVA':
            Solicitud.objects.filter(pk=solicitud.pk).update(estado='PENDIENTE')
            SolicitudHistorial.objects.create(
                solicitud=solicitud,
                estado_anterior='ACTIVA',
                estado_nuevo='PENDIENTE',
            )

        messages.success(request, "Asignación eliminada correctamente.")
        return redirect("asignacion_list")

    return render(request, "asignaciones/asignacion_confirm_delete.html", {
        "asignacion": asignacion
    })