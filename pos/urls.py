from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_dashboard, name='dashboard'),
    path('api/scan/', views.api_scan_card, name='api_scan'),
    path('api/checkout/', views.api_checkout, name='api_checkout'),
]
