from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'users'

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/users/user/', permanent=False), name='user_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('menu-permissions/', views.user_menu_permissions_view, name='user_menu_permissions'),
    path('api/search-users/', views.api_search_users, name='api_search_users'),
    path('api/toggle-user-menu/', views.api_toggle_user_menu, name='api_toggle_user_menu'),
]
