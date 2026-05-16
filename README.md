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

2. Copy `.env.example` to `.env` and set database values.

3. Run database scripts in `database/` (start with `00_RUN_ALL.sql`).

4. Migrate and run the server:

```bash
python manage.py migrate
python manage.py runserver
```

Default superuser (from seed data): `superadmin` / `Admin@123`

## Main modules

- **POS** — sales checkout and token generation
- **Kitchen** — order queue (KDS)
- **Distribution** — pickup counter
- **Balance** — employee advance, credit, allocations
- **Inventory** — menu, daily stock, waste
- **Admin** — master data and settings (`/admin/`)
