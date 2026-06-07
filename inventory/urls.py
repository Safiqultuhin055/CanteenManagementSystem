from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('menu-item/<int:pk>/image/', views.menu_item_image, name='menu_item_image'),
    path('menu-item/<int:pk>/image', views.menu_item_image, name='menu_item_image_no_slash'),
]
