"""Authentication services aligned with SQL Server stored procedures."""
import logging

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


def get_client_meta(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    user_agent = (request.META.get('HTTP_USER_AGENT') or '')[:500]
    return ip or None, user_agent or None


def get_security_setting(key, default):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 setting_value
                FROM system_settings
                WHERE setting_key = %s AND is_active = 1
                """,
                [key],
            )
            row = cursor.fetchone()
            return row[0] if row else default
    except Exception as exc:
        logger.debug('Could not read setting %s: %s', key, exc)
        return default


def _validate_user_login(username, ip_address, user_agent):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            EXEC dbo.usp_ValidateUserLogin
                @Username = %s,
                @IPAddress = %s,
                @UserAgent = %s
            """,
            [username, ip_address, user_agent],
        )
        columns = [col[0] for col in cursor.description] if cursor.description else []
        row = cursor.fetchone()
    if not row:
        return None
    return dict(zip(columns, row))


def record_login_success(user_id, ip_address, user_agent, session_key):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            EXEC dbo.usp_RecordLoginSuccess
                @UserId = %s,
                @IPAddress = %s,
                @UserAgent = %s,
                @SessionKey = %s
            """,
            [user_id, ip_address, user_agent, session_key],
        )


def record_login_failure(username, ip_address, reason):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            EXEC dbo.usp_RecordLoginFailure
                @Username = %s,
                @IPAddress = %s,
                @Reason = %s
            """,
            [username, ip_address, reason],
        )


def end_user_session(session_key):
    if not session_key:
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_sessions
                SET logout_at = SYSDATETIME(),
                    is_active = 0,
                    last_activity = SYSDATETIME()
                WHERE session_key = %s AND is_active = 1
                """,
                [session_key],
            )
            cursor.execute(
                """
                UPDATE login_history
                SET logout_at = SYSDATETIME(),
                    session_duration = DATEDIFF(SECOND, login_at, SYSDATETIME())
                WHERE id = (
                    SELECT TOP 1 lh.id
                    FROM login_history lh
                    INNER JOIN user_sessions us ON us.user_id = lh.user_id
                    WHERE us.session_key = %s
                      AND lh.login_status = 'SUCCESS'
                      AND lh.logout_at IS NULL
                    ORDER BY lh.login_at DESC
                )
                """,
                [session_key],
            )
    except Exception as exc:
        logger.warning('Could not end user session: %s', exc)


def change_user_password(user, new_password, changed_by_id, ip_address, reason='SELF_CHANGE'):
    new_hash = make_password(new_password)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            EXEC dbo.usp_ChangePassword
                @UserId = %s,
                @NewPasswordHash = %s,
                @ChangedBy = %s,
                @Reason = %s,
                @IPAddress = %s
            """,
            [user.pk, new_hash, changed_by_id, reason, ip_address],
        )
        row = cursor.fetchone()
    if row and row[0] == 0:
        return False, row[1] if len(row) > 1 else 'Password change failed'
    user.refresh_from_db()
    return True, 'Password changed successfully'


def password_was_used_recently(user, new_password, count=5):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP (%s) password_hash
                FROM password_history
                WHERE user_id = %s
                ORDER BY changed_at DESC
                """,
                [count, user.pk],
            )
            rows = cursor.fetchall()
        for (old_hash,) in rows:
            if check_password(new_password, old_hash):
                return True
        if user.password and check_password(new_password, user.password):
            return True
    except Exception as exc:
        logger.debug('Password history check skipped: %s', exc)
    return False


def authenticate_user(request, username, password):
    """
    Validate via usp_ValidateUserLogin, verify password, record success/failure.
    Returns (user, error_message).
    """
    username = (username or '').strip()
    if not username or not password:
        return None, 'Please enter username and password.'

    ip_address, user_agent = get_client_meta(request)

    try:
        result = _validate_user_login(username, ip_address, user_agent)
    except Exception as exc:
        logger.exception('Login validation failed')
        return None, 'Unable to connect to authentication service. Please try again.'

    if not result:
        return None, 'Invalid username or password.'

    success = result.get('Success') or result.get('success')
    if not success or int(success) == 0:
        message = result.get('Message') or result.get('message') or 'Invalid username or password.'
        return None, message

    user_id = result.get('id')
    try:
        user = User.objects.get(pk=user_id, is_deleted=False)
    except User.DoesNotExist:
        record_login_failure(username, ip_address, 'USER_NOT_FOUND')
        return None, 'Invalid username or password.'

    if user.locked_until and user.locked_until > timezone.now():
        return None, 'Account is temporarily locked. Try again later or contact admin.'

    if not check_password(password, user.password):
        try:
            record_login_failure(username, ip_address, 'INVALID_PASSWORD')
            user.refresh_from_db(fields=['failed_login_count', 'locked_until'])
        except Exception:
            pass
        if user.locked_until and user.locked_until > timezone.now():
            return None, 'Too many failed attempts. Account is locked temporarily.'
        return None, 'Invalid username or password.'

    return user, None
