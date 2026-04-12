from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from apps.muelles.models import Muelle, Espacio, EtiquetaMuelle, ZonaTierra
from apps.asignaciones.models import Asignacion
from apps.solicitudes.models import Solicitud


@login_required
def mapa_view(request):
    return render(request, 'mapa/mapa.html')


@login_required
def disponibilidad_json(request):
    fecha_str = request.GET.get('fecha')
    solicitud_id = request.GET.get('solicitud_id')

    fecha = parse_date(fecha_str) if fecha_str else None

    # Espacios ocupados en esa fecha
    ocupados = set()
    if fecha:
        asignaciones = Asignacion.objects.filter(
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha,
        ).prefetch_related('espacios')
        for a in asignaciones:
            for e in a.espacios.all():
                ocupados.add(e.id)

    # Datos de la embarcación si viene con solicitud
    eslora = manga = None
    if solicitud_id:
        try:
            sol = Solicitud.objects.select_related(
                'embarcacion'
            ).get(pk=solicitud_id)
            eslora = float(sol.embarcacion.eslora)
            manga  = float(sol.embarcacion.manga)
        except Solicitud.DoesNotExist:
            pass

    # Construir respuesta de espacios
    espacios_data = []
    for e in Espacio.objects.select_related('muelle').all():
        # Calcular estado
        if e.id in ocupados:
            estado = 'ocupado'
        elif eslora and manga:
            # 1px = 10cm → metros = px / 10
            largo_m = float(e.alto)  / 10
            ancho_m = float(e.ancho) / 10
            cabe = largo_m >= eslora and ancho_m >= manga
            if not cabe:
                estado = 'no_cabe'
            else:
                sobra_largo = largo_m - eslora
                sobra_ancho = ancho_m - manga
                porcentaje_sobrante = ((sobra_largo * sobra_ancho) /
                                       (largo_m * ancho_m)) * 100
                if porcentaje_sobrante <= 30:
                    estado = 'ideal'
                else:
                    estado = 'posible'
        else:
            estado = 'libre'

        espacios_data.append({
            'id':         e.id,
            'numero':     e.numero,
            'muelle_id':  e.muelle_id,
            'muelle':     e.muelle.nombre,
            'pos_x':      float(e.pos_x),
            'pos_y':      float(e.pos_y),
            'ancho':      float(e.ancho),
            'alto':       float(e.alto),
            'rotacion':   float(e.rotacion),
            'es_pasillo': e.es_pasillo,
            'estado':     estado,
        })

    # Zonas de tierra
    zonas = list(ZonaTierra.objects.values('id','puntos','color','nombre'))

    # Etiquetas
    etiquetas = list(EtiquetaMuelle.objects.values(
        'id','muelle_id','pos_x','pos_y','texto','tamanio','color'
    ))

    return JsonResponse({
        'espacios':  espacios_data,
        'zonas':     zonas,
        'etiquetas': etiquetas,
        'fecha':     fecha_str,
        'eslora':    eslora,
        'manga':     manga,
    })


@login_required
def asignar_espacio(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    import json
    from django.db import transaction
    from apps.asignaciones.models import Administrador

    try:
        data         = json.loads(request.body)
        solicitud_id = int(data['solicitud_id'])
        espacio_ids  = data['espacio_ids']   # lista de IDs
        fecha_inicio = parse_date(data['fecha_inicio'])
        fecha_fin    = parse_date(data['fecha_fin'])
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    try:
        administrador = Administrador.objects.get(user=request.user)
    except Administrador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no es administrador'}, status=403)

    try:
        solicitud = Solicitud.objects.get(pk=solicitud_id)
        espacios  = Espacio.objects.filter(id__in=espacio_ids)
        muelle    = espacios.first().muelle

        with transaction.atomic():
            asignacion = Asignacion.objects.create(
                solicitud     = solicitud,
                muelle        = muelle,
                administrador = administrador,
                fecha_inicio  = fecha_inicio,
                fecha_fin     = fecha_fin,
            )
            asignacion.espacios.set(espacios)
            asignacion.validar_traslape_espacios()

        return JsonResponse({'ok': True, 'asignacion_id': asignacion.pk})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
