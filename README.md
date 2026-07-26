# Royal Brothers Fitness Gym

A full-stack gym membership website built with Flask (Python) and MySQL: member registration with email verification, secure login with brute-force lockout, membership plan requests, an admin dashboard, and a public contact form.

## Features

- **Member accounts** — registration, login/logout, profile editing, profile photo upload
- **Email verification** — new accounts are unverified until the user clicks a link sent via Gmail SMTP; unverified accounts cannot log in
- **Login security** — accounts are locked for 15 minutes after 5 consecutive failed password attempts
- **Forgot / reset password** — secure, time-limited, single-use reset links sent by email
- **Membership plans** — browse plans, request one, admin approves/rejects
- **Admin dashboard** — separate admin login, manage members (verified only), membership plans, membership requests, and contact messages, with live stats
- **Contact form** — public inquiry form, viewable/markable-as-read by admin
- **Security practices** — Werkzeug password hashing (no plaintext passwords anywhere), hashed single-use tokens for email verification/password reset, all secrets read from environment variables (nothing hardcoded)

## Project Structure

```
royal-brothers-gym/
├── app/                          # Application package
│   ├── __init__.py               # create_app() factory: config, Flask-Mail, blueprints, static serving
│   ├── config.py                 # Reads all settings from environment variables
│   ├── extensions.py             # MySQL connection helper
│   ├── models.py                 # All database queries
│   ├── routes/                   # Flask blueprints (one file per feature area)
│   │   ├── auth_routes.py        # Register, login, logout, profile, email verification, password reset
│   │   ├── admin_routes.py       # Admin login + dashboard endpoints
│   │   ├── membership_routes.py  # Plans + membership requests
│   │   ├── contact_routes.py     # Public contact form
│   │   └── reservation_routes.py # Slot booking (present, not yet wired into the app — see note below)
│   └── static/                   # Entire frontend: HTML pages, CSS, JS, images
│       └── uploads/profile_photos/  # User-uploaded profile photos (gitignored, folder kept via .gitkeep)
├── schema/
│   ├── schema.sql                # Full schema — use for a brand-new database
│   └── schema_updates.sql        # Migration — use only if you have an existing database with data
├── scripts/
│   └── create_admin.py           # One-time CLI script to create your first admin account
├── wsgi.py                       # Server entry point (`gunicorn wsgi:app`)
├── requirements.txt
├── runtime.txt                   # Python version pin for Render/Railway
├── Procfile                      # `web: gunicorn wsgi:app`
├── .env.example                  # Template for required environment variables
└── .gitignore
```

This is a **monolith**: Flask serves both the JSON API (under `/api/...`) and the static frontend (plain HTML/CSS/JS, no templating engine) from the same app. There's no build step for the frontend.

## Local Setup

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) (for sending verification/reset emails)

### 1. Clone and install dependencies
```bash
git clone <your-repo-url>
cd royal-brothers-gym
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up the database
Create the database and tables:
```bash
mysql -u root -p < schema/schema.sql
```
(If you're migrating an existing database instead of starting fresh, use `schema/schema_updates.sql` — see the comments inside it.)

### 3. Configure environment variables
```bash
cp .env.example .env
```
Then edit `.env` with your real values — see [Environment Variables](#environment-variables) below.

### 4. Create your first admin account
```bash
python scripts/create_admin.py
```
Follow the prompts to set an admin username/password.

### 5. Run the app
```bash
python wsgi.py
```
Visit `http://127.0.0.1:5000`.

## Environment Variables

All configuration is read from environment variables (see `app/config.py`). None are hardcoded anywhere in the codebase.

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DB_HOST` | No (default `localhost`) | MySQL host |
| `DB_USER` | No (default `root`) | MySQL user |
| `DB_PASSWORD` | Yes | MySQL password |
| `DB_NAME` | No (default `royal_brothers_gym`) | MySQL database name |
| `DB_PORT` | No (default `3306`) | MySQL port |
| `MAIL_USERNAME` | Yes | Gmail address used to send emails |
| `MAIL_PASSWORD` | Yes | Gmail **App Password** (not your normal Gmail password) |
| `MAIL_SENDER_NAME` | No | Display name for outgoing emails |
| `APP_BASE_URL` | No | Your deployed domain (e.g. `https://yourgym.com`), used to build verification/reset links. Falls back to the incoming request's host if unset |

If a required variable is missing, the app raises a clear error at startup instead of silently running with an insecure default.

## Deployment

The app is a standard WSGI app (`wsgi:app`), so it deploys the same way on any Python host.

### Render / Railway (recommended — persistent Python service + easy MySQL)
1. Push this repo to GitHub.
2. Create a new **Web Service** (Render) or **Project → Deploy from GitHub** (Railway).
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn wsgi:app` (already in `Procfile`, most platforms auto-detect it)
5. Add all variables from [Environment Variables](#environment-variables) in the platform's dashboard — **do not upload your `.env` file**.
6. Provision a MySQL database (Railway has a one-click MySQL plugin; on Render, use an external MySQL provider such as PlanetScale, or Railway's MySQL alongside a Render web service) and point `DB_HOST`/`DB_USER`/`DB_PASSWORD`/`DB_NAME`/`DB_PORT` at it.
7. Run `schema/schema.sql` against that database once, then `python scripts/create_admin.py` locally pointed at the production DB (or via the platform's shell/console) to create your admin account.
8. Set `APP_BASE_URL` to your deployed URL so verification/reset emails link to the right place.

### Vercel
Vercel's Python support is serverless-function based, which is a good fit for stateless APIs but a mismatch for this app's design (server-rendered static pages + MySQL connections opened per-request + server-side session cookies). It's **not the recommended host for this project as-is**. If you specifically want the frontend on Vercel:
- Deploy the `app/static/` folder to Vercel as a static site, and
- Deploy the Flask API (this repo, minus static serving) to Render/Railway separately, then point the frontend's `fetch()` calls at that API's URL instead of relative paths.

That split requires code changes beyond this restructuring (CORS configuration, updating every `fetch()` base URL, cross-domain cookies for sessions), so it's called out here rather than done silently — ask if you'd like that split built out.

## Notes

- **`app/routes/reservation_routes.py`** exists in the codebase but is **not currently registered** in `app/__init__.py`, and it references model functions (`create_reservation`, `get_reservations_by_user`, `update_reservation_status`) that don't exist yet in `app/models.py`. It was carried over as-is during this reorganization without being wired up, since doing so would mean building a new feature rather than restructuring existing ones. Let me know if you'd like this feature completed.
- The `.env` file that was in the original project (and an `env.example` with real credentials filled in instead of placeholders) have **not** been carried into this restructured copy — see the security note you were given separately regarding rotating those credentials.
