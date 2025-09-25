from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("print/", views.print_pdf, name="print_pdf"),
    path('elimina-prodotto/<int:pk>/', views.elimina_prodotto, name="elimina_prodotto"),
]
