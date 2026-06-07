"""
DEPRECATED when using shared SQL Server (.env.shared.example).
LocalDB -> Docker sync is only needed for the old split-database setup.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pyodbc

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOCAL_CONN = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=(localdb)\\MSSQLLocalDB;'
    'DATABASE=CanteenManagementDB;'
    'Trusted_Connection=yes;TrustServerCertificate=yes;'
)
DOCKER_CONN = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=127.0.0.1,1433;'
    'DATABASE=CanteenManagementDB;'
    'UID=sa;PWD=FabulousSql2024!;TrustServerCertificate=yes;'
)


def fetchall(cur, sql):
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def sync_employees(local, docker):
    rows = fetchall(
        local,
        """
        SELECT employee_code, first_name, last_name, full_name, email, phone, department_id,
               designation, employee_type, is_active, is_deleted
        FROM dbo.employees
        WHERE is_deleted = 0
        """,
    )
    upserted = 0
    for row in rows:
        docker.execute(
            'SELECT id FROM dbo.employees WHERE employee_code = ?',
            [row['employee_code']],
        )
        existing = docker.fetchone()
        if existing:
            docker.execute(
                """
                UPDATE dbo.employees SET
                    first_name = ?, last_name = ?, full_name = ?, email = ?, phone = ?,
                    department_id = ?, designation = ?, employee_type = ?, is_active = ?, is_deleted = ?
                WHERE id = ?
                """,
                [
                    row['first_name'], row['last_name'], row['full_name'], row['email'], row['phone'],
                    row['department_id'], row['designation'], row['employee_type'], row['is_active'], row['is_deleted'],
                    existing[0],
                ],
            )
        else:
            docker.execute(
                """
                INSERT INTO dbo.employees (
                    employee_code, first_name, last_name, full_name, email, phone, department_id,
                    designation, employee_type, is_active, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    row['employee_code'], row['first_name'], row['last_name'], row['full_name'], row['email'],
                    row['phone'], row['department_id'], row['designation'], row['employee_type'],
                    row['is_active'], row['is_deleted'],
                ],
            )
        upserted += 1
    print(f'  employees: {upserted} synced')


def sync_employee_cards(local, docker):
    rows = fetchall(
        local,
        """
        SELECT e.employee_code, ec.card_number, ec.card_type, ec.card_status, ec.is_active, ec.is_deleted
        FROM dbo.employee_cards ec
        INNER JOIN dbo.employees e ON e.id = ec.employee_id
        WHERE ec.is_deleted = 0
        """,
    )
    updated = 0
    inserted = 0
    for row in rows:
        docker.execute(
            'SELECT id FROM dbo.employees WHERE employee_code = ? AND is_deleted = 0',
            [row['employee_code']],
        )
        emp = docker.fetchone()
        if not emp:
            continue
        employee_id = emp[0]
        docker.execute(
            'SELECT id FROM dbo.employee_cards WHERE employee_id = ? AND is_deleted = 0',
            [employee_id],
        )
        existing = docker.fetchone()
        if existing:
            docker.execute(
                """
                UPDATE dbo.employee_cards
                SET card_number = ?, card_type = ?, card_status = ?, is_active = ?
                WHERE id = ?
                """,
                [row['card_number'], row['card_type'], row['card_status'], row['is_active'], existing[0]],
            )
            updated += 1
        else:
            docker.execute(
                """
                INSERT INTO dbo.employee_cards (employee_id, card_number, card_type, card_status, is_active, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [employee_id, row['card_number'], row['card_type'], row['card_status'], row['is_active'], row['is_deleted']],
            )
            inserted += 1
    print(f'  employee_cards: {updated} updated, {inserted} inserted')


def sync_menu_images(local, docker):
    rows = fetchall(
        local,
        """
        SELECT item_code, image_path
        FROM dbo.menu_items
        WHERE image_path IS NOT NULL AND LTRIM(RTRIM(image_path)) <> ''
        """,
    )
    for row in rows:
        docker.execute(
            """
            UPDATE dbo.menu_items
            SET image_path = ?
            WHERE item_code = ?
            """,
            [row['image_path'], row['item_code']],
        )
    print(f'  menu_items.image_path: {len(rows)} synced')


def sync_daily_stock(local, docker):
    docker.execute('DELETE FROM dbo.daily_food_stock WHERE stock_date = CAST(SYSDATETIME() AS DATE)')
    rows = fetchall(
        local,
        """
        SELECT mi.item_code, dfs.stock_date, dfs.prepared_quantity, dfs.sold_quantity, dfs.remaining_quantity,
               dfs.is_active, dfs.is_deleted, dfs.created_by, dfs.updated_by
        FROM dbo.daily_food_stock dfs
        INNER JOIN dbo.menu_items mi ON mi.id = dfs.menu_item_id
        WHERE dfs.stock_date = CAST(SYSDATETIME() AS DATE) AND dfs.is_deleted = 0
        """,
    )
    inserted = 0
    for row in rows:
        docker.execute('SELECT id FROM dbo.menu_items WHERE item_code = ?', [row['item_code']])
        item = docker.fetchone()
        if not item:
            continue
        docker.execute(
            """
            INSERT INTO dbo.daily_food_stock (
                menu_item_id, stock_date, prepared_quantity, sold_quantity, remaining_quantity,
                is_active, is_deleted, created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                item[0], row['stock_date'], row['prepared_quantity'], row['sold_quantity'],
                row['remaining_quantity'], row['is_active'], row['is_deleted'], row['created_by'], row['updated_by'],
            ],
        )
        inserted += 1
    print(f'  daily_food_stock (today): {inserted} synced')


def main():
    print('Syncing LocalDB -> Docker SQL (CanteenManagementDB)…')
    with pyodbc.connect(LOCAL_CONN, autocommit=False) as lconn, pyodbc.connect(DOCKER_CONN, autocommit=False) as dconn:
        local = lconn.cursor()
        docker = dconn.cursor()
        sync_employees(local, docker)
        sync_employee_cards(local, docker)
        sync_menu_images(local, docker)
        sync_daily_stock(local, docker)
        dconn.commit()
    print('Done.')


if __name__ == '__main__':
    main()
