"""Business calendar date aligned with SQL Server (same as POS orders/queues)."""

from django.db import connection


def get_business_date():
    with connection.cursor() as cursor:
        cursor.execute('SELECT CAST(SYSDATETIME() AS DATE)')
        return cursor.fetchone()[0]
