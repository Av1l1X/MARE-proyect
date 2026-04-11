from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.muelle_list,   name='muelle_list'),
    path('nuevo/',              views.muelle_create, name='muelle_create'),
    path('<int:pk>/',           views.muelle_detail, name='muelle_detail'),
    path('<int:pk>/editar/',   views.muelle_update, name='muelle_update'),
    path('<int:pk>/eliminar/', views.muelle_delete, name='muelle_delete'),

    # Editor visual de espacios
    path('<int:pk>/espacios/json/',    views.muelle_espacios_json,    name='muelle_espacios_json'),
    path('<int:pk>/espacios/guardar/', views.muelle_espacios_guardar, name='muelle_espacios_guardar'),

    path('editor-global/',           views.editor_global,           name='editor_global'),
    path('zonas/json/',              views.zonas_tierra_json,        name='zonas_tierra_json'),
    path('zonas/guardar/',           views.zonas_tierra_guardar,     name='zonas_tierra_guardar'),
    
    path('etiquetas/json/',    views.etiquetas_json,    name='etiquetas_json'),
    path('etiquetas/guardar/', views.etiquetas_guardar, name='etiquetas_guardar'),
]