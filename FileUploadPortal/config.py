"""
config.py
---------
Central configuration for the FileUploadPortal Flask application.
Keeping configuration in one place makes the project easier to maintain
and deploy across different environments (development / production).
"""

import os

# BASE_DIR points to the root of the project (where this file lives).
# It is used to build absolute paths for the SQLite database file.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Base configuration class.
    Values can be overridden using environment variables for production
    deployments without changing any code.
    """

    # Secret key used by Flask to sign session cookies and flash messages.
    # IMPORTANT: Change this to a strong random value in production and
    # set it via an environment variable instead of hardcoding it.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLite database file stored at the project root as "database.db".
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "database.db")
    )

    # Disable SQLAlchemy event system overhead we don't use.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Limit maximum upload size to 50 MB to avoid memory abuse from very
    # large file uploads. Adjust as needed for your use case.
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    # Session cookie hardening (kept permissive enough for local/VS Code dev).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
