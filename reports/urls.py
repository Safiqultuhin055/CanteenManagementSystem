from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_hub, name='reports_hub'),
    path('sales/', views.sales_report, name='sales_report'),
]
