from django.shortcuts               import get_object_or_404, redirect, render
from django.core.paginator          import Paginator, PageNotAnInteger, EmptyPage
from django.contrib                 import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions         import ValidationError
from apps.clientes.models           import Cliente
from .models                        import Embarcacion, TipoBarco


@login_required
def embarcacion_list(request):
    embarcaciones = Embarcacion.objects.select_related(
        'cliente', 'tipo_barco'
    ).order_by('nombre_bote')
    q = request.GET.get('q', '')
    if q:
        embarcaciones = embarcaciones.filter(nombre_bote__icontains=q) | \
                        embarcaciones.filter(cliente__fullname__icontains=q)
    paginator = Paginator(embarcaciones, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'embarcaciones/embarcacion_list.html', {
        'page_obj': page_obj, 'embarcaciones': page_obj.object_list,
        'q': q, 'query_params': f'&q={q}' if q else '',
    })


@login_required
def embarcacion_detail(request, pk):
    embarcacion = get_object_or_404(
        Embarcacion.objects.select_related('cliente', 'tipo_barco'), pk=pk
    )
    return render(request, 'embarcaciones/embarcacion_detail.html', {
        'embarcacion': embarcacion,
        'solicitudes': embarcacion.solicitudes.order_by('-fecha_solicitud')[:5],
    })


@login_required
def embarcacion_create(request):
    context = {
        'clientes':    Cliente.objects.order_by('fullname'),
        'tipos_barco': TipoBarco.objects.order_by('tipo_barco'),
    }
    if request.method == 'POST':
        embarcacion = Embarcacion(
            cliente_id    = request.POST.get('cliente'),
            tipo_barco_id = request.POST.get('tipo_barco'),
            nombre_bote   = request.POST.get('nombre_bote', '').strip(),
            eslora        = request.POST.get('eslora'),
            manga         = request.POST.get('manga'),
            calado        = request.POST.get('calado'),
        )
        try:
            embarcacion.full_clean()
            embarcacion.save()
            messages.success(request, 'Embarcación registrada correctamente.')
            return redirect('embarcacion_detail', pk=embarcacion.pk)
        except ValidationError as exc:
            context['errors']      = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            context['embarcacion'] = embarcacion
    return render(request, 'embarcaciones/embarcacion_form.html', context)


@login_required
def embarcacion_update(request, pk):
    embarcacion = get_object_or_404(Embarcacion, pk=pk)
    context = {
        'embarcacion': embarcacion,
        'clientes':    Cliente.objects.order_by('fullname'),
        'tipos_barco': TipoBarco.objects.order_by('tipo_barco'),
    }
    if request.method == 'POST':
        embarcacion.cliente_id    = request.POST.get('cliente')
        embarcacion.tipo_barco_id = request.POST.get('tipo_barco')
        embarcacion.nombre_bote   = request.POST.get('nombre_bote', '').strip()
        embarcacion.eslora        = request.POST.get('eslora')
        embarcacion.manga         = request.POST.get('manga')
        embarcacion.calado        = request.POST.get('calado')
        try:
            embarcacion.full_clean()
            embarcacion.save()
            messages.success(request, 'Embarcación actualizada correctamente.')
            return redirect('embarcacion_detail', pk=embarcacion.pk)
        except ValidationError as exc:
            context['errors'] = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
    return render(request, 'embarcaciones/embarcacion_form.html', context)


@login_required
def embarcacion_delete(request, pk):
    embarcacion = get_object_or_404(Embarcacion, pk=pk)
    if request.method == 'POST':
        try:
            embarcacion.delete()
            messages.success(request, 'Embarcación eliminada correctamente.')
            return redirect('embarcacion_list')
        except Exception:
            messages.error(request, 'No se puede eliminar: tiene solicitudes registradas.')
            return redirect('embarcacion_detail', pk=pk)
    return render(request, 'embarcaciones/embarcacion_confirm_delete.html', {'embarcacion': embarcacion})