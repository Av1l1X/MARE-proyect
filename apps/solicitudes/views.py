from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST  

from apps.embarcaciones.models import Embarcacion
from .models import Solicitud

@login_required
def solicitud_list(request):
    solicitudes = Solicitud.objects.select_related(
        "embarcacion",
        "embarcacion__cliente",
        "embarcacion__tipo_barco"
    ).all().order_by("-fecha_solicitud", "-id")

    estado_filter = request.GET.get("estado", "")
    if estado_filter:
        solicitudes = solicitudes.filter(estado=estado_filter)

    paginator = Paginator(solicitudes, 10)
    numero_pagina = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(numero_pagina)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    query_params = ""
    if estado_filter:
        query_params += f"&estado={estado_filter}"

    context = {
        "page_obj": page_obj,
        "solicitudes": page_obj.object_list,
        "estados": Solicitud.ESTADOS,
        "estado_filter": estado_filter,
        "query_params": query_params,
    }
    return render(request, "solicitudes/solicitud_list.html", context)

@login_required
def solicitud_detail(request, pk):
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            "embarcacion__cliente",
            "embarcacion__tipo_barco",
        ),
        pk=pk
    )

    return render(request, 'solicitudes/solicitud_detail.html', {
        'solicitud':   solicitud,
        'historial':   solicitud.historial.order_by('-fecha_cambio'),
        'asignaciones': solicitud.asignaciones.select_related(
            'muelle', 'administrador__user'  # ← administrador__user no solo administrador
        ).order_by('-fecha_inicio'),

    })

@login_required
def solicitud_create(request):
    embarcaciones = Embarcacion.objects.select_related("cliente", "tipo_barco").all().order_by("nombre_bote")
    context = {
        "embarcaciones": embarcaciones,
        "estados": Solicitud.ESTADOS,
    }

    if request.method == 'POST':
        solicitud = Solicitud(
            embarcacion_id = request.POST.get('embarcacion'),
            fecha_llegada  = request.POST.get('fecha_llegada'),
            fecha_salida   = request.POST.get('fecha_salida'),
            comentario     = request.POST.get('comentario', '').strip(),
            estado         = request.POST.get('estado') or 'PENDIENTE',
        )

        try:
            solicitud.full_clean()
            solicitud.save()
            messages.success(request, "Solicitud creada correctamente.")
            return redirect("solicitud_list")
        except ValidationError as exc:
            context["errors"] = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            context["solicitud"] = solicitud

    return render(request, "solicitudes/solicitud_form.html", context)

@login_required
def solicitud_update(request, pk):
    solicitud = get_object_or_404(Solicitud, pk=pk)
    embarcaciones = Embarcacion.objects.select_related("cliente", "tipo_barco").all().order_by("nombre_bote")

    context = {
        "solicitud": solicitud,
        "embarcaciones": embarcaciones,
        "estados": Solicitud.ESTADOS,
    }

    if request.method == "POST":
        solicitud.embarcacion_id = request.POST.get("embarcacion")
        solicitud.fecha_llegada = request.POST.get("fecha_llegada")
        solicitud.fecha_salida = request.POST.get("fecha_salida")
        solicitud.comentario = request.POST.get("comentario", "").strip()
        solicitud.estado = request.POST.get("estado") or solicitud.estado

        try:
            solicitud.full_clean()
            solicitud.save()
            messages.success(request, "Solicitud actualizada correctamente.")
            return redirect("solicitud_detail", pk=solicitud.pk)
        except ValidationError as exc:
            context["errors"] = exc.message_dict if hasattr(exc, "message_dict") else exc.messages

    return render(request, "solicitudes/solicitud_form.html", context)

@login_required
def solicitud_delete(request, pk):
    solicitud = get_object_or_404(Solicitud, pk=pk)

    if request.method == "POST":
        solicitud.delete()
        messages.success(request, "Solicitud eliminada correctamente.")
        return redirect("solicitud_list")

    return render(request, "solicitudes/solicitud_confirm_delete.html", {
        "solicitud": solicitud
    })

@login_required
@require_POST
def solicitud_cambiar_estado(request, pk, nuevo_estado):
    solicitud = get_object_or_404(Solicitud, pk=pk)

    estados_validos = [estado[0] for estado in Solicitud.ESTADOS]
    
    if nuevo_estado not in estados_validos:
        messages.error(request, "Estado no válido.")
        return redirect("solicitud_detail", pk=pk)

    solicitud.estado = nuevo_estado

    try:
        solicitud.full_clean()
        solicitud.save()
        messages.success(request, f'Solicitud actualizada a {solicitud.get_estado_display()}.')
    except ValidationError as exc:
      for error in (exc.messages if hasattr(exc, 'messages') else [str(exc)]):
            messages.error(request, error)

    return redirect("solicitud_detail", pk=pk)