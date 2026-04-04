from django.urls import path
from . import views

urlpatterns = [
    path("", views.solicitud_list, name="solicitud_list"),
    path("nuevo/", views.solicitud_create, name="solicitud_create"),
    path("<int:pk>/", views.solicitud_detail, name="solicitud_detail"),
    path("<int:pk>/editar/", views.solicitud_update, name="solicitud_update"),
    path("<int:pk>/eliminar/", views.solicitud_delete, name="solicitud_delete"),

    path("<int:pk>/estado/<str:nuevo_estado>/", views.solicitud_cambiar_estado, name="solicitud_cambiar_estado"),
]