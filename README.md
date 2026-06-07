# Canteen Management System

Django-based canteen management for employees: POS, kitchen (KDS), distribution, balance/credit, inventory, and admin settings. Uses Microsoft SQL Server.

## Requirements

- Python 3.12+
- SQL Server (LocalDB or full instance)
- ODBC Driver 17 for SQL Server

## Setup

1. Clone the repository and create a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.shared.example` to `.env` (shared SQL Server — recommended for team/LAN):

```bash
copy .env.shared.example .env
```

Shared server (local dev **and** Docker use the same database):

| Setting | Value |
|---------|-------|
| Host | `192.168.153.248` |
| Database | `CanteenManagementDB` |
| User | `sa` |

Run **either** local `runserver` **or** Docker — not both at once (same DB).

3. Run database scripts in `database/` on the server if the DB is new (see `deploy/docker/init-db.ps1`).

4. Migrate and run locally:

```bash
python manage.py migrate
python manage.py runserver
```

## Docker (LAN host on port 365)

```powershell
powershell -ExecutionPolicy Bypass -File deploy\docker\docker-start.ps1
```

Open: http://192.168.120.51:365/users/login/

Uses the same `CanteenManagementDB` on `192.168.153.248` as local dev.

Default superuser (from seed data): `superadmin` / `Admin@123`

## Main modules

- **POS** — sales checkout and token generation
- **Kitchen** — order queue (KDS)
- **Distribution** — pickup counter
- **Balance** — employee advance, credit, allocations
- **Inventory** — menu, daily stock, waste
- **Admin** — master data and settings (`/admin/`)
