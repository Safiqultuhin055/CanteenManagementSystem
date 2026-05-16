from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, PasswordChangeForm
from .services.auth_service import (
    authenticate_user,
    change_user_password,
    end_user_session,
    get_security_setting,
    password_was_used_recently,
    record_login_success,
)


def _safe_next_url(request, next_url):
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


def login_view(request):
    if request.user.is_authenticated and not request.user.must_change_password:
        return redirect('core:dashboard')

    next_url = _safe_next_url(request, request.GET.get('next') or request.POST.get('next'))

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user, error = authenticate_user(
                request,
                form.cleaned_data['username'],
                form.cleaned_data['password'],
            )
            if user:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                if form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(60 * 60 * 24 * 14)
                else:
                    request.session.set_expiry(0)

                try:
                    from .services.auth_service import get_client_meta
                    ip_address, user_agent = get_client_meta(request)
                    record_login_success(
                        user.pk,
                        ip_address,
                        user_agent,
                        request.session.session_key,
                    )
                except Exception:
                    pass

                user.refresh_from_db(fields=['must_change_password', 'full_name'])

                if user.must_change_password:
                    messages.warning(request, 'Please set a new password to continue.')
                    return redirect('users:password_change')

                messages.success(request, f"Welcome back, {user.full_name or user.username}!")
                if next_url:
                    return redirect(next_url)
                return redirect('core:dashboard')

            messages.error(request, error or 'Login failed.')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {
        'form': form,
        'next': next_url or '',
        'max_attempts': get_security_setting('MAX_LOGIN_ATTEMPTS', '5'),
        'lockout_minutes': get_security_setting('ACCOUNT_LOCKOUT_MINUTES', '30'),
        'min_password_length': get_security_setting('PASSWORD_MIN_LENGTH', '8'),
    })


def logout_view(request):
    session_key = request.session.session_key
    if session_key:
        end_user_session(session_key)
    logout(request)
    messages.info(request, 'You have been signed out successfully.')
    return redirect('users:login')


@login_required
def password_change_view(request):
    forced = request.user.must_change_password
    min_len = int(get_security_setting('PASSWORD_MIN_LENGTH', '8'))
    history_count = int(get_security_setting('PASSWORD_HISTORY_COUNT', '5'))

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            if password_was_used_recently(request.user, new_password, history_count):
                messages.error(
                    request,
                    f'You cannot reuse any of your last {history_count} passwords.',
                )
            else:
                from .services.auth_service import get_client_meta
                ip_address, _ = get_client_meta(request)
                ok, msg = change_user_password(
                    request.user,
                    new_password,
                    request.user.pk,
                    ip_address,
                )
                if ok:
                    request.user.refresh_from_db()
                    messages.success(request, msg)
                    return redirect('core:dashboard')
                messages.error(request, msg)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/password_change.html', {
        'form': form,
        'forced': forced,
        'min_password_length': min_len,
    })
