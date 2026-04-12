from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import Muelle, Espacio

import json
from django.http import JsonResponse
from django.views.decorators.http  import require_POST



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

#Configuracion para hacer la creaxcion del mapa de mairna


@login_required
def muelle_espacios_json(request, pk):
    # API GET — devuelve todos los espacios del muelle en JSON
    muelle = get_object_or_404(Muelle, pk=pk)
    espacios = list(
        muelle.espacios.values(
            'id', 'numero',
            'pos_x', 'pos_y',
            'ancho', 'alto',
            'rotacion', 'es_pasillo', 'activo',
        )
    )
    return JsonResponse({
        'muelle': {
            'id':     muelle.pk,
            'nombre': muelle.nombre,
        },
        'espacios': espacios,
    })

@login_required
@require_POST
def muelle_espacios_guardar(request, pk):
    muelle = get_object_or_404(Muelle, pk=pk)

    try:
        data = json.loads(request.body)
        espacios_data = data.get('espacios', [])
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    if not isinstance(espacios_data, list) or len(espacios_data) == 0:
        return JsonResponse({'ok': False, 'error': 'Se requiere al menos un espacio'}, status=400)

    # Validar duplicados en el payload antes de tocar la BD
    from collections import Counter
    numeros = [int(e['numero']) for e in espacios_data 
                if not e.get('es_pasillo') and e.get('numero') is not None]  
    dupes = [n for n, c in Counter(numeros).items() if c > 1]
    if dupes:
        return JsonResponse({
            'ok': False,
            'error': f'Números de espacio duplicados: {dupes}. Cada espacio debe tener un número único por muelle.'
        }, status=400)

    # Verificar asignaciones activas
    if muelle.espacios.filter(asignaciones__isnull=False).exists():
        numeros_con_asignacion = list(
            muelle.espacios.filter(asignaciones__isnull=False)
            .values_list('numero', flat=True).distinct()
        )
        return JsonResponse({
            'ok': False,
            'error': f'Los espacios {numeros_con_asignacion} tienen asignaciones activas.'
        }, status=400)

    try:
        from django.db import transaction
        with transaction.atomic():
            muelle.espacios.all().delete()
            nuevos = [
                Espacio(
                    muelle     = muelle,
                    numero     = None if bool(e.get('es_pasillo', False)) else int(e['numero']),
                    pos_x      = float(e['pos_x']),
                    pos_y      = float(e['pos_y']),
                    ancho      = float(e['ancho']),
                    alto       = float(e['alto']),
                    rotacion   = float(e.get('rotacion', 0)),
                    es_pasillo = bool(e.get('es_pasillo', False)),
                    activo     = bool(e.get('activo', True)),
                )
                for e in espacios_data
            ]
            Espacio.objects.bulk_create(nuevos)
            muelle.total_espacios = len([e for e in espacios_data if not e.get('es_pasillo')])
            muelle.save(update_fields=['total_espacios'])

        return JsonResponse({'ok': True, 'total': len(nuevos)})

    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

@login_required
def zonas_tierra_json(request):
    from .models import ZonaTierra
    zonas = list(ZonaTierra.objects.values('id','nombre','puntos','color'))
    return JsonResponse({'zonas': zonas})

@login_required
@require_POST
def zonas_tierra_guardar(request):
    from .models import ZonaTierra
    import json
    try:
        data  = json.loads(request.body)
        zonas = data.get('zonas', [])
        ZonaTierra.objects.all().delete()
        for z in zonas:
            ZonaTierra.objects.create(
                puntos = json.dumps(z['puntos']),
                color  = z.get('color', '#7ab648'),
                nombre = z.get('nombre', ''),
            )
        return JsonResponse({'ok': True, 'total': len(zonas)})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

@login_required
def editor_global(request):
    from apps.muelles.models import Muelle
    muelles = Muelle.objects.filter(estado=True).order_by('nombre')
    return render(request, 'muelles/editor_global.html', {'muelles': muelles})


@login_required
def etiquetas_json(request):
    from .models import EtiquetaMuelle
    etiquetas = list(
        EtiquetaMuelle.objects.select_related('muelle').values(
            'id', 'muelle_id', 'pos_x', 'pos_y', 'texto', 'tamanio', 'color'
        )
    )
    return JsonResponse({'etiquetas': etiquetas})


@login_required
@require_POST
def etiquetas_guardar(request):
    from .models import EtiquetaMuelle
    try:
        data = json.loads(request.body)
        etiquetas_data = data.get('etiquetas', [])
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    try:
        from django.db import transaction
        with transaction.atomic():
            for e in etiquetas_data:
                muelle_id = int(e['muelle_id'])
                EtiquetaMuelle.objects.update_or_create(
                    muelle_id=muelle_id,
                    defaults={
                        'pos_x':   float(e.get('pos_x', 0)),
                        'pos_y':   float(e.get('pos_y', 0)),
                        'texto':   str(e.get('texto', '')),
                        'tamanio': int(e.get('tamanio', 14)),
                        'color':   str(e.get('color', '#ffffff')),
                    }
                )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    