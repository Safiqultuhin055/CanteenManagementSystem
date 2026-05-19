from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.kds_dashboard, name='kds_dashboard'),
    path('api/queue/', views.api_get_queue, name='api_get_queue'),
    path('api/stream/', views.api_kitchen_stream, name='api_kitchen_stream'),
    path('api/update/', views.api_update_status, name='api_update_status'),
]
