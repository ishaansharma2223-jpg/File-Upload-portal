"""
app/__init__.py
---------------
Application factory for FileUploadPortal.

Using the factory pattern (create_app) instead of a single global Flask
instance makes the project easier to test and keeps configuration,
extension setup, and blueprint registration cleanly organized.
"""

from flask import Flask

from app.extensions import db
from config import Config


def create_app(config_class: type = Config) -> Flask:
    """Build and configure the Flask application instance."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app instance.
    db.init_app(app)

    # Import and register blueprints. Imports happen here (rather than at
    # module load time) to avoid circular-import issues, since the route
    # modules import models/extensions that depend on `db` being ready.
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.user.routes import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(user_bp, url_prefix="/user")

    # Create database tables (if they do not already exist) and seed a
    # default administrator account so the project is runnable out of
    # the box, with zero manual setup steps.
    with app.app_context():
        from app import models  # noqa: F401  (ensures models are registered)

        db.create_all()
        _seed_default_admin()

    return app


def _seed_default_admin() -> None:
    """Create a default admin account on first run, if none exists yet."""

    from werkzeug.security import generate_password_hash

    from app.models import Admin

    if Admin.query.count() == 0:
        default_admin = Admin(
            username="admin",
            password_hash=generate_password_hash("admin123"),
        )
        db.session.add(default_admin)
        db.session.commit()

        print("=" * 64)
        print("FileUploadPortal: default admin account created.")
        print("    Username: admin")
        print("    Password: admin123")
        print("Please log in and change this password as soon as possible.")
        print("=" * 64)
