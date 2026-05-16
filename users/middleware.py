from django.shortcuts import redirect
from django.urls import reverse


class MustChangePasswordMiddleware:
    """Redirect authenticated users who must change password before using the app."""

    EXEMPT_PREFIXES = (
        '/users/login/',
        '/users/logout/',
        '/users/password-change/',
        '/static/',
        '/admin/login/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'must_change_password', False):
            path = request.path
            if not any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
                change_url = reverse('users:password_change')
                if path != change_url:
                    return redirect('users:password_change')
        return self.get_response(request)
