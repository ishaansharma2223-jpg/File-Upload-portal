# FileUploadPortal

A production-ready, fully-commented **Flask + SQLAlchemy + SQLite** web
application for routing user-uploaded files into admin-configured
destination folders, based on a selected Platform, Company, and Upload
Type (Active / Block / Inactive / Archive).

## Features

### Admin
- Login
- Dashboard (summary stats + recent uploads)
- User Management (create, activate/deactivate, delete)
- Platform Management (create / delete)
- Company Management (create / delete)
- Destination Folder Management (configure 4 physical paths per
  platform + company combination)
- Upload Logs (browse + filter by username/status)

### User
- Login
- Platform Selection
- Company Selection
- Upload Screen (choose Upload Type + source file)

### Business Logic
- **Destination folder** = entirely **admin-configured**, per
  (Platform, Company) pair, with 4 sub-paths: Active, Block, Inactive,
  Archive.
- **Source file** = chosen by the user on the Upload screen.
- Every upload (success or failure) is recorded in the `UploadLog`
  table with username, platform, company, file name, file type,
  status, upload date, and upload time.

## Project Structure

```
FileUploadPortal/
├── run.py                     # App entry point
├── config.py                  # Configuration (DB URI, secret key, etc.)
├── seed.py                    # Optional script to add sample data
├── requirements.txt
├── database.db                # Created automatically on first run
├── app/
│   ├── __init__.py             # Application factory
│   ├── extensions.py           # Shared SQLAlchemy instance
│   ├── models.py                # Admin, User, Platform, Company, FolderPath, UploadLog
│   ├── utils.py                 # admin_required / user_required decorators
│   ├── auth/
│   │   └── routes.py            # Landing page, admin login, user login, logout
│   ├── admin/
│   │   └── routes.py            # Dashboard + all admin management screens
│   ├── user/
│   │   └── routes.py            # Platform/company selection + upload
│   ├── templates/
│   │   ├── base.html            # Shared layout (Bootstrap 5 navbar, flash messages)
│   │   ├── index.html           # Landing page
│   │   ├── auth/                # admin_login.html, user_login.html
│   │   ├── admin/                # dashboard, users, platforms, companies, folders, logs
│   │   └── user/                 # platform_select, company_select, upload
│   └── static/
│       └── css/style.css        # Minor custom styling on top of Bootstrap
```

## Company Access Control (per-user restriction)

By default, **every user can access every company** that has a folder
configuration for the platform they select — they only ever see
companies the admin has actually linked to that platform, never the
full company list.

If you want a specific user locked to just **one** company:

1. Go to **Admin → User Management**.
2. When creating the user, choose a specific company under
   **Company Access** (instead of leaving it on "All Companies").
3. For an existing user, use the **Company Access** dropdown directly
   in their table row and click the checkmark to save.

A restricted user will only ever see that one company on the Company
Selection screen — and only if the admin has also configured a folder
path for that company under the platform the user picked.

> **Upgrading an existing install:** this feature adds a new
> `restricted_company_id` column to the `users` table. If you already
> have a `database.db` file from before this change, delete it (or
> drop the `users` table) and restart the app so SQLAlchemy recreates
> the schema — otherwise you'll see a "no such column" error.

## Setup

1. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   python run.py
   ```

   The app starts at **http://127.0.0.1:5000/**. On first launch, the
   SQLite database (`database.db`) and all tables are created
   automatically, and a default admin account is seeded:

   - **Username:** `admin`
   - **Password:** `admin123`

   Please log in and treat this as a placeholder credential to be
   rotated/replaced for any real deployment.

4. **(Optional) Seed sample data** for quick manual testing — two
   platforms, two companies, a folder configuration, and a test user
   (`testuser` / `test123`):

   ```bash
   python seed.py
   ```

## Usage Walkthrough

1. Log in as **admin** (`admin` / `admin123`).
2. Go to **Platforms** and add at least one platform (e.g. "Web Portal").
3. Go to **Companies** and add at least one company (e.g. "Acme Corp").
4. Go to **Destination Folder Management** and configure the four
   destination paths (Active / Block / Inactive / Archive) for that
   platform + company pair.
5. Go to **User Management** and create a regular user account.
6. Log out, then log back in as that **user**.
7. Select the platform, then the company, then on the Upload screen
   pick an **Upload Type** and a file to upload.
8. The file is saved into the folder path the admin configured for
   that exact platform/company/upload-type combination, and the
   action is recorded in **Upload Logs** (visible to the admin).

## Notes for VS Code

- Open the `FileUploadPortal` folder directly in VS Code.
- Select your virtual environment's Python interpreter
  (Command Palette → "Python: Select Interpreter").
- Use the built-in terminal to run `python run.py`.
- `database.db` and any folders referenced by your folder
  configurations will be created automatically at runtime — no manual
  setup needed beyond installing dependencies.

## Tech Stack

- **Flask 3** — web framework
- **Flask-SQLAlchemy** — ORM, backed by **SQLite**
- **Werkzeug** — password hashing (`generate_password_hash` /
  `check_password_hash`) and secure filename handling
- **Bootstrap 5** (via CDN) — responsive UI, including Bootstrap Icons
