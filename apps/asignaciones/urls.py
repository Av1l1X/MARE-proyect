from django.urls import path
from . import views

urlpatterns = [
    path("", views.asignacion_list, name="asignacion_list"),
    path("nuevo/", views.asignacion_create, name="asignacion_create"),
    path("<int:pk>/", views.asignacion_detail, name="asignacion_detail"),
    path("<int:pk>/editar/", views.asignacion_update, name="asignacion_update"),
    path("<int:pk>/eliminar/", views.asignacion_delete, name="asignacion_delete"),
]