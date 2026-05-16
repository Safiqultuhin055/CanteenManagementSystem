from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'core'

    def ready(self):
        from core.django_compat import patch_django_template_context_copy
        patch_django_template_context_copy()
        from core.admin_base import setup_admin_site
        setup_admin_site()
        import core.admin  # noqa: F401
