from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.exceptions import ValidationError

from apps.solicitudes.models import Solicitud
from apps.muelles.models import Muelle
from .models import Asignacion


def asignacion_list(request):
    asignaciones = Asignacion.objects.select_related(
        "solicitud",
        "solicitud__embarcacion",
        "solicitud__embarcacion__cliente",
        "muelle",
        "administrador",
    ).all().order_by("-fecha_inicio", "-id")

    paginator = Paginator(asignaciones, 10)
    numero_pagina = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(numero_pagina)
    except:
        page_obj = paginator.page(1)

    context = {
        "page_obj": page_obj,
        "asignaciones": page_obj.object_list,
    }
    return render(request, "asignaciones/asignacion_list.html", context)


def asignacion_detail(request, pk):
    asignacion = get_object_or_404(
        Asignacion.objects.select_related(
            "solicitud",
            "solicitud__embarcacion",
            "solicitud__embarcacion__cliente",
            "muelle",
            "administrador",
        ),
        pk=pk
    )

    return render(request, "asignaciones/asignacion_detail.html", {
        "asignacion": asignacion
    })


def asignacion_create(request):
    solicitudes = Solicitud.objects.select_related(
        "embarcacion",
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
        solicitud_id = request.POST.get("solicitud")
        muelle_id = request.POST.get("muelle")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        pos_inicio = request.POST.get("pos_inicio")
        pos_fin = request.POST.get("pos_fin")

        asignacion = Asignacion(
            solicitud_id=solicitud_id,
            muelle_id=muelle_id,
            administrador=request.user,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            pos_inicio=pos_inicio,
            pos_fin=pos_fin,
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


def asignacion_update(request, pk):
    asignacion = get_object_or_404(Asignacion, pk=pk)

    solicitudes = Solicitud.objects.select_related(
        "embarcacion",
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


def asignacion_delete(request, pk):
    asignacion = get_object_or_404(Asignacion, pk=pk)

    if request.method == "POST":
        solicitud = asignacion.solicitud
        asignacion.delete()

        if not solicitud.asignaciones.exists() and solicitud.estado == "ACTIVA":
            solicitud.estado = "PENDIENTE"
            solicitud.save()

        messages.success(request, "Asignación eliminada correctamente.")
        return redirect("asignacion_list")

    return render(request, "asignaciones/asignacion_confirm_delete.html", {
        "asignacion": asignacion
    })