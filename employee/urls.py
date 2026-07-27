from django.urls import path

from . import views

app_name = 'employee'

urlpatterns = [
    path('api/face/save/', views.api_face_save, name='api_face_save'),
    path('api/face/status/', views.api_face_status, name='api_face_status'),
    path('api/face/delete/', views.api_face_delete, name='api_face_delete'),
]
