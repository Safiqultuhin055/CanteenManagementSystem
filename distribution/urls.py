from django.urls import path
from . import views

app_name = 'distribution'

urlpatterns = [
    path('', views.distribution_dashboard, name='distribution_dashboard'),
    path('display/', views.token_display, name='token_display'),
    path('api/tokens/', views.api_get_tokens, name='api_get_tokens'),
    path('api/call/', views.api_call_token, name='api_call_token'),
    path('api/deliver/', views.api_mark_delivered, name='api_mark_delivered'),
]
