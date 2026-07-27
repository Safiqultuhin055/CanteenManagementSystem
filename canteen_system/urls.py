"""
URL configuration for canteen_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='core:dashboard', permanent=False)),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('', include('core.urls', namespace='core')),
    path('pos/', include('pos.urls', namespace='pos')),
    path('kitchen/', include('kitchen.urls', namespace='kitchen')),
    path('distribution/', include('distribution.urls', namespace='distribution')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('employee/', include('employee.urls', namespace='employee')),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            'docs/diagrams/<path:path>',
            serve,
            {'document_root': settings.BASE_DIR / 'docs' / 'diagrams'},
        ),
    ]

# Media uploads (menu images) — serve in Docker/LAN even when DEBUG=False
urlpatterns += [
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
