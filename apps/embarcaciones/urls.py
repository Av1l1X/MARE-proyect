from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.embarcacion_list,   name='embarcacion_list'),
    path('nuevo/',              views.embarcacion_create, name='embarcacion_create'),
    path('<int:pk>/',           views.embarcacion_detail, name='embarcacion_detail'),
    path('<int:pk>/editar/',   views.embarcacion_update, name='embarcacion_update'),
    path('<int:pk>/eliminar/', views.embarcacion_delete, name='embarcacion_delete'),
]