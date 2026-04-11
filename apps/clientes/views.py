from django.shortcuts               import get_object_or_404, redirect, render
from django.core.paginator          import Paginator, PageNotAnInteger, EmptyPage
from django.contrib                 import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions         import ValidationError
from .models                        import Cliente


@login_required
def cliente_list(request):
    clientes = Cliente.objects.order_by('fullname')
    q = request.GET.get('q', '')
    if q:
        clientes = clientes.filter(fullname__icontains=q) | clientes.filter(email__icontains=q)
    paginator = Paginator(clientes, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'clientes/cliente_list.html', {
        'page_obj': page_obj, 'clientes': page_obj.object_list,
        'q': q, 'query_params': f'&q={q}' if q else '',
    })


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/cliente_detail.html', {
        'cliente': cliente,
        'embarcaciones': cliente.embarcaciones.select_related('tipo_barco').order_by('nombre_bote'),
    })


@login_required
def cliente_create(request):
    context = {}
    if request.method == 'POST':
        cliente = Cliente(
            fullname = request.POST.get('fullname', '').strip(),
            email    = request.POST.get('email', '').strip(),
            telefono = request.POST.get('telefono', '').strip(),
        )
        try:
            cliente.full_clean()
            cliente.save()
            messages.success(request, 'Cliente creado correctamente.')
            return redirect('cliente_detail', pk=cliente.pk)
        except ValidationError as exc:
            context['errors']  = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            context['cliente'] = cliente
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    context = {'cliente': cliente}
    if request.method == 'POST':
        cliente.fullname = request.POST.get('fullname', '').strip()
        cliente.email    = request.POST.get('email', '').strip()
        cliente.telefono = request.POST.get('telefono', '').strip()
        try:
            cliente.full_clean()
            cliente.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('cliente_detail', pk=cliente.pk)
        except ValidationError as exc:
            context['errors'] = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, 'Cliente eliminado correctamente.')
            return redirect('cliente_list')
        except Exception:
            # PROTECT en embarcaciones lanza ProtectedError
            messages.error(request, 'No se puede eliminar: el cliente tiene embarcaciones registradas.')
            return redirect('cliente_detail', pk=pk)
    return render(request, 'clientes/cliente_confirm_delete.html', {'cliente': cliente})