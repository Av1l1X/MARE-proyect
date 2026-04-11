from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import Muelle


@login_required
def muelle_list(request):
    muelles = Muelle.objects.order_by('nombre')
    paginator = Paginator(muelles, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'muelles/muelle_list.html', {
        'page_obj': page_obj, 'muelles': page_obj.object_list,
    })


@login_required
def muelle_detail(request, pk):
    muelle = get_object_or_404(Muelle, pk=pk)
    return render(request, 'muelles/muelle_detail.html', {
        'muelle':      muelle,
        'asignaciones': muelle.asignaciones.select_related(
            'solicitud__embarcacion__cliente', 'administrador__user'
        ).order_by('-fecha_inicio')[:10],
    })


@login_required
def muelle_create(request):
    context = {}
    if request.method == 'POST':
        muelle = Muelle(
            nombre         = request.POST.get('nombre', '').strip(),
            tam_maximo     = request.POST.get('tam_maximo'),
            total_espacios = request.POST.get('total_espacios'),
            estado         = request.POST.get('estado') == 'on',
            coordenada_x   = request.POST.get('coordenada_x'),
            coordenada_y   = request.POST.get('coordenada_y'),
        )
        try:
            muelle.full_clean()
            muelle.save()
            messages.success(request, 'Muelle creado correctamente.')
            return redirect('muelle_detail', pk=muelle.pk)
        except ValidationError as exc:
            context['errors'] = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            context['muelle'] = muelle
    return render(request, 'muelles/muelle_form.html', context)


@login_required
def muelle_update(request, pk):
    muelle  = get_object_or_404(Muelle, pk=pk)
    context = {'muelle': muelle}
    if request.method == 'POST':
        muelle.nombre         = request.POST.get('nombre', '').strip()
        muelle.tam_maximo     = request.POST.get('tam_maximo')
        muelle.total_espacios = request.POST.get('total_espacios')
        muelle.estado         = request.POST.get('estado') == 'on'
        muelle.coordenada_x   = request.POST.get('coordenada_x')
        muelle.coordenada_y   = request.POST.get('coordenada_y')
        try:
            muelle.full_clean()
            muelle.save()
            messages.success(request, 'Muelle actualizado correctamente.')
            return redirect('muelle_detail', pk=muelle.pk)
        except ValidationError as exc:
            context['errors'] = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
    return render(request, 'muelles/muelle_form.html', context)


@login_required
def muelle_delete(request, pk):
    muelle = get_object_or_404(Muelle, pk=pk)
    if request.method == 'POST':
        try:
            muelle.delete()
            messages.success(request, 'Muelle eliminado correctamente.')
            return redirect('muelle_list')
        except Exception:
            messages.error(request, 'No se puede eliminar: el muelle tiene asignaciones.')
            return redirect('muelle_detail', pk=pk)
    return render(request, 'muelles/muelle_confirm_delete.html', {'muelle': muelle})