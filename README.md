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

- **POS** — RFID/NFC card checkout, cash/guest orders, voice ordering, token generation
- **Kitchen** — order queue (KDS)
- **Distribution** — pickup counter
- **Balance** — employee advance, credit, allocations
- **Inventory** — menu, daily stock, waste
- **Admin** — master data and settings (`/admin/`), API integrations, system settings

## Roles & access

Seeded roles (`database/09_seed_data.sql`), resolved via `users/permissions.py`:

| Role | Code | Access |
|------|------|--------|
| Super Administrator | `SUPER_ADMIN` | Full system |
| Administrator | `ADMIN` | Administrative |
| Manager | `MANAGER` | Management |
| Cashier | `CASHIER` | POS / billing |
| Kitchen Staff | `KITCHEN` | KDS |
| Distribution Staff | `DISTRIBUTION` | Pickup counter |

Menu/permission gating is DB-driven (`roles`, `permissions`, `role_permissions`,
plus per-user `user_permissions` / `user_menu_grants`).

## POS checkout modes

- **Card** — scan RFID/NFC; charges the employee balance/credit.
- **Guest (cash)** — walk-in cash sale, no card. The **Guest** toggle is
  **role-gated**: visible only to `SUPER_ADMIN`, `ADMIN`, `CASHIER`. Other roles
  never see it, and the checkout API rejects guest orders from unauthorized roles
  (`pos/views.py` → `api_checkout`, `users.permissions.can_use_guest_mode`).

## Voice ordering (AI)

Bangla voice/text ordering in the POS (`pos/services/voice_agent.py`). The **Voice**
button shows whenever any LLM provider is configured — no code flag, fully DB-driven
via **Admin → API integrations** (`core.api_registry.get_active_llm`).

Supported providers (tried best-first, with fallthrough on failure):

- **Anthropic (Claude)** — native tool calling
- **Google (Gemini)** — JSON schema response
- **Local / self-hosted gateway** — `POST {base_url}/v1/chat` with `X-API-KEY`,
  body `{model, prompt, stream}`; the model returns a single JSON turn

Configure each provider's key, model, and `base_url` in the admin. Set `is_default`
to pick the primary; inactive rows are skipped. If the active provider is
unreachable the assistant shows **"Voice assistant unreachable"** — check the
provider's `base_url` is running and reachable from the app host.
