from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_dashboard, name='dashboard'),
    path('api/scan/', views.api_scan_card, name='api_scan'),
    path('api/checkout/', views.api_checkout, name='api_checkout'),
    path('api/voice-order/', views.api_voice_order, name='api_voice_order'),
    path('api/tts/', views.api_tts, name='api_tts'),
    path('api/voice-provider/', views.api_voice_provider, name='api_voice_provider'),
]
