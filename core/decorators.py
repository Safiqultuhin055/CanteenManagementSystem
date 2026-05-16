from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from users.permissions import user_has_permission


def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if user_has_permission(request.user, permission_code):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('core:dashboard')
        return _wrapped
    return decorator
