from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'core'

# Menu paths from seed data → Django Admin (until dedicated CRUD pages exist)
ADMIN_REDIRECTS = [
    ('orders/', '/admin/pos/order/'),
    ('employees/', '/admin/employee/employee/'),
    ('cards/', '/admin/employee/employeecard/'),
    ('balance/', '/admin/balance/employeebalance/'),
    ('menu-items/', '/admin/inventory/menuitem/'),
    ('categories/', '/admin/inventory/foodcategory/'),
    ('daily-stock/', '/admin/inventory/dailyfoodstock/'),
    ('raw-materials/', '/admin/inventory/rawmaterial/'),
    ('suppliers/', '/admin/inventory/supplier/'),
    ('waste/', '/admin/inventory/wasterecord/'),
    ('purchases/', '/admin/'),
    ('roles/', '/admin/users/role/'),
    ('departments/', '/admin/employee/department/'),
    ('audit-logs/', '/admin/'),
    ('guest-cards/', '/admin/pos/guestcard/'),
    ('tokens/', '/distribution/display/'),
]

urlpatterns = [
    path('settings/', views.settings_hub, name='settings'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('help/user-manual/', views.help_user_manual, name='help_user_manual'),
    path('help/technical/', views.help_technical, name='help_technical'),
    path('help/diagrams/', views.help_diagrams, name='help_diagrams'),
]

urlpatterns += [
    path(route, RedirectView.as_view(url=target, permanent=False))
    for route, target in ADMIN_REDIRECTS
]
