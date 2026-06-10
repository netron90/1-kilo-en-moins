from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('reussites/', views.reussites, name='reussites'),
    path('generer-plan/', views.generer_plan, name='generer_plan'),
    path('telecharger-pdf/', views.telecharger_pdf, name='telecharger_pdf'),
    path('valider-paiement/', views.valider_paiement, name='valider_paiement'),
]