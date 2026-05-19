from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_hub, name='reports_hub'),
    path('daily/', views.daily_sales, name='daily_sales'),
    path('user-wise/', views.user_wise_sales, name='user_wise'),
    path('monthly/', views.monthly_summary, name='monthly_summary'),
    path('inventory/', views.inventory_status, name='inventory_status'),
    path('sales/', views.sales_report, name='sales_report'),
]
