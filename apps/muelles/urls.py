from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.muelle_list,   name='muelle_list'),
    path('nuevo/',              views.muelle_create, name='muelle_create'),
    path('<int:pk>/',           views.muelle_detail, name='muelle_detail'),
    path('<int:pk>/editar/',   views.muelle_update, name='muelle_update'),
    path('<int:pk>/eliminar/', views.muelle_delete, name='muelle_delete'),
]