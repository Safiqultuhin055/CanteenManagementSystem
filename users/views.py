from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods

from users.db_schema import ensure_user_access_schema
from users.permissions import is_admin_user, user_has_permission

from .forms import LoginForm, PasswordChangeForm
from .models import User
from .services.menu_permission_service import (
    backfill_menu_grants_from_permissions,
    build_nested_menu_tree,
    ensure_menu_permission_mappings,
    ensure_user_menu_access_nav,
    save_user_menu_permissions,
    search_users,
    toggle_user_menu_access,
)
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


def _can_assign_user_menus(user) -> bool:
    if not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False) or is_admin_user(user):
        return True
    return user_has_permission(user, 'USER_MENU_ASSIGN')


@login_required
@require_http_methods(['GET', 'POST'])
def user_menu_permissions_view(request):
    if not _can_assign_user_menus(request.user):
        return HttpResponseForbidden('You cannot assign user menu permissions.')

    selected_user = None
    user_id = request.GET.get('user') or request.POST.get('user_id')
    search_q = (request.GET.get('q') or request.POST.get('q') or '').strip()

    if user_id:
        try:
            selected_user = get_object_or_404(
                User, pk=int(user_id), is_deleted=False, is_active=True,
            )
        except (TypeError, ValueError):
            selected_user = None

    if request.method == 'POST' and selected_user:
        if selected_user.is_superuser:
            messages.error(request, 'Superuser access is not managed here.')
        else:
            menu_ids = request.POST.getlist('menu_ids')
            count = save_user_menu_permissions(
                selected_user.pk,
                menu_ids,
                request.user.pk,
            )
            messages.success(
                request,
                f'Saved menu access for {selected_user}. {count} permission(s) granted.',
            )
        return redirect(f'{reverse("users:user_menu_permissions")}?user={selected_user.pk}&q={search_q}')

    ensure_user_access_schema()
    ensure_user_menu_access_nav()
    ensure_menu_permission_mappings()

    users = search_users(search_q, limit=25)
    if selected_user:
        backfill_menu_grants_from_permissions(selected_user.pk, request.user.pk)
    menu_tree = build_nested_menu_tree(selected_user.pk if selected_user else None)

    return render(request, 'users/user_menu_permissions.html', {
        'users': users,
        'selected_user': selected_user,
        'menu_tree': menu_tree,
        'search_q': search_q,
    })


@login_required
@require_GET
def api_search_users(request):
    if not _can_assign_user_menus(request.user):
        return JsonResponse({'results': []}, status=403)
    q = (request.GET.get('q') or '').strip()
    results = [
        {
            'id': u.pk,
            'username': u.username,
            'full_name': u.full_name or '',
            'label': f'{u.full_name or u.username} ({u.username})',
        }
        for u in search_users(q, limit=15)
    ]
    return JsonResponse({'results': results})


@login_required
@require_http_methods(['POST'])
def api_toggle_user_menu(request):
    if not _can_assign_user_menus(request.user):
        return JsonResponse({'ok': False, 'error': 'Forbidden'}, status=403)
    try:
        user_id = int(request.POST.get('user_id', ''))
        menu_id = int(request.POST.get('menu_id', ''))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Invalid user or menu id'}, status=400)

    target = get_object_or_404(User, pk=user_id, is_deleted=False, is_active=True)
    if target.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Cannot modify superuser menus'}, status=400)

    grant = request.POST.get('grant') in ('1', 'true', 'on', 'yes')
    result = toggle_user_menu_access(user_id, menu_id, grant, request.user.pk)
    status = 200 if result.get('ok') else 400
    return JsonResponse(result, status=status)
