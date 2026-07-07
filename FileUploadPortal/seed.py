"""
seed.py
-------
Optional helper script to populate the database with sample data for
quick manual testing: a couple of platforms, companies, a test user,
and a destination-folder configuration pointing at local "uploads/"
subfolders (created automatically on first use).

This is NOT required to run the app - app/__init__.py already seeds a
default admin account automatically on first launch. Run this script
only if you want extra sample data to play with immediately:

    python seed.py
"""

import os

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Company, FolderPath, Platform, User

app = create_app()

with app.app_context():
    base_uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")

    # --- Sample platforms -------------------------------------------------
    platform_names = ["Web Portal", "Mobile App"]
    platforms = {}
    for name in platform_names:
        platform = Platform.query.filter_by(name=name).first()
        if not platform:
            platform = Platform(name=name)
            db.session.add(platform)
            db.session.flush()
        platforms[name] = platform

    # --- Sample companies ---------------------------------------------------
    company_names = ["Acme Corp", "Globex Inc"]
    companies = {}
    for name in company_names:
        company = Company.query.filter_by(name=name).first()
        if not company:
            company = Company(name=name)
            db.session.add(company)
            db.session.flush()
        companies[name] = company

    db.session.commit()

    # --- Sample folder configuration for Web Portal + Acme Corp -----------
    platform = platforms["Web Portal"]
    company = companies["Acme Corp"]

    existing = FolderPath.query.filter_by(
        platform_id=platform.id, company_id=company.id
    ).first()

    if not existing:
        prefix = os.path.join(base_uploads_dir, "web_portal", "acme_corp")
        db.session.add(
            FolderPath(
                platform_id=platform.id,
                company_id=company.id,
                active_path=os.path.join(prefix, "active"),
                block_path=os.path.join(prefix, "block"),
                inactive_path=os.path.join(prefix, "inactive"),
                archive_path=os.path.join(prefix, "archive"),
            )
        )

    # --- Sample test user ---------------------------------------------------
    if not User.query.filter_by(username="testuser").first():
        db.session.add(
            User(username="testuser", password_hash=generate_password_hash("test123"))
        )

    db.session.commit()

    print("=" * 64)
    print("Sample data seeded successfully:")
    print("  Platforms: Web Portal, Mobile App")
    print("  Companies: Acme Corp, Globex Inc")
    print("  Test user: testuser / test123")
    print(f"  Folder config: Web Portal + Acme Corp -> {base_uploads_dir}")
    print("=" * 64)
