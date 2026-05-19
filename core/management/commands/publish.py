"""
Prepare the app for LAN / production use (migrate, static files, permission sync).
"""
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Publish: migrate DB, collect static files, sync menu permissions, run deploy checks. '
        'Use --serve to start Waitress on 0.0.0.0 after publish.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--skip-migrate', action='store_true', help='Skip database migrations.')
        parser.add_argument('--skip-static', action='store_true', help='Skip collectstatic.')
        parser.add_argument('--skip-permissions', action='store_true', help='Skip permission/menu sync.')
        parser.add_argument(
            '--serve',
            action='store_true',
            help='Start Waitress WSGI server after publish (bind with --bind).',
        )
        parser.add_argument(
            '--bind',
            default='0.0.0.0:8000',
            help='Host:port for --serve (default: 0.0.0.0:8000).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Publishing Canteen Management System…'))

        if not options['skip_migrate']:
            self.stdout.write('-> migrate')
            call_command('migrate', '--noinput', verbosity=options['verbosity'])

        if not options['skip_static']:
            if not getattr(settings, 'STATIC_ROOT', None):
                raise CommandError(
                    'STATIC_ROOT is not set in settings. Cannot run collectstatic.',
                )
            self.stdout.write('-> collectstatic')
            call_command('collectstatic', '--noinput', verbosity=options['verbosity'])

        if not options['skip_permissions']:
            self.stdout.write('-> ensure_user_permissions_table')
            try:
                call_command('ensure_user_permissions_table', verbosity=options['verbosity'])
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'  skipped: {exc}'))
            self.stdout.write('-> sync_menu_permissions')
            call_command('sync_menu_permissions', verbosity=options['verbosity'])

        self.stdout.write('-> check --deploy')
        call_command('check', '--deploy', verbosity=options['verbosity'])

        self._print_notes()

        if options['serve']:
            self._serve(options['bind'])

        self.stdout.write(self.style.SUCCESS('Publish complete.'))

    def _print_notes(self):
        hosts = ', '.join(settings.ALLOWED_HOSTS) or '(empty)'
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Settings:'))
        self.stdout.write(f'  DEBUG = {settings.DEBUG}')
        self.stdout.write(f'  ALLOWED_HOSTS = {hosts}')
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                '  Set DEBUG=False in .env for real production.',
            ))
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Run on LAN / TV (after publish):'))
        self.stdout.write('  py -3 manage.py publish --serve')
        self.stdout.write('  py -3 manage.py publish --serve --bind 0.0.0.0:8080')
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('.env for other PCs on network:'))
        self.stdout.write('  ALLOWED_HOSTS=127.0.0.1,localhost,YOUR_PC_IP')
        self.stdout.write('  DEBUG=False')
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('IIS hosting: see deploy/iis/IIS_HOSTING.txt'))

    def _serve(self, bind: str):
        if ':' in bind:
            host, port = bind.rsplit(':', 1)
        else:
            host, port = bind, '8000'
        try:
            from waitress import serve
            from django.core.wsgi import get_wsgi_application
        except ImportError as exc:
            raise CommandError(
                'Waitress is not installed. Run: pip install waitress',
            ) from exc
        self.stdout.write(self.style.NOTICE(f'Starting Waitress on http://{host}:{port}/'))
        serve(get_wsgi_application(), host=host, port=int(port))
