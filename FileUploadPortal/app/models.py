"""
models.py
---------
SQLAlchemy ORM models for the FileUploadPortal application.

Tables:
    Admin       - Administrator accounts that manage the platform.
    User        - End-user accounts that upload files.
    Platform    - Selectable platforms (e.g. "Web", "Mobile", "API").
    Company     - Selectable companies / clients.
    FolderPath  - Admin-configured destination folders for each
                  (platform, company) pair, one path per upload type.
    UploadLog   - Audit trail of every file uploaded by every user.
"""

from datetime import datetime

from app.extensions import db


class Admin(db.Model):
    """Administrator account used to log into the admin dashboard."""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Admin {self.username}>"


class User(db.Model):
    """End-user account that selects a platform/company and uploads files."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Controls whether the user is allowed to log in. Managed by the admin
    # in the User Management screen.
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Company access control:
    #   - NULL (default) -> the user can see/select ANY company that has
    #     a folder configuration for the platform they pick. This is the
    #     default, unrestricted behaviour for all users.
    #   - Set to a Company.id -> the user is locked to that ONE company
    #     only, on every platform. The admin sets this from the User
    #     Management screen for users who should not see other companies.
    restricted_company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True
    )
    restricted_company = db.relationship("Company", foreign_keys=[restricted_company_id])

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Platform(db.Model):
    """A selectable platform, configured by the admin (e.g. Web, Mobile)."""

    __tablename__ = "platforms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # One platform can have many folder-path configurations (one per company).
    folder_paths = db.relationship(
        "FolderPath", backref="platform", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Platform {self.name}>"


class Company(db.Model):
    """A selectable company/client, configured by the admin."""

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # One company can have many folder-path configurations (one per platform).
    folder_paths = db.relationship(
        "FolderPath", backref="company", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company {self.name}>"


class FolderPath(db.Model):
    """
    Admin-configured destination folder paths.

    Each (platform_id, company_id) combination maps to exactly one row,
    which defines the four physical destination folders that a user's
    uploaded file can be routed into, depending on the upload type they
    choose on the upload screen: Active, Block, Inactive, or Archive.
    """

    __tablename__ = "folder_paths"

    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey("platforms.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    active_path = db.Column(db.String(500), nullable=False)
    block_path = db.Column(db.String(500), nullable=False)
    inactive_path = db.Column(db.String(500), nullable=False)
    archive_path = db.Column(db.String(500), nullable=False)

    # Ensure only one folder configuration exists per platform/company pair.
    __table_args__ = (
        db.UniqueConstraint("platform_id", "company_id", name="uix_platform_company"),
    )

    def path_for(self, upload_type: str) -> str:
        """Return the destination path that matches the given upload type."""
        mapping = {
            "Active": self.active_path,
            "Block": self.block_path,
            "Inactive": self.inactive_path,
            "Archive": self.archive_path,
        }
        return mapping.get(upload_type)

    def __repr__(self):
        return f"<FolderPath platform={self.platform_id} company={self.company_id}>"


class UploadLog(db.Model):
    """
    Audit record created every time a user uploads a file.
    Stores denormalized platform/company names so that historical logs
    remain readable even if a platform or company is later renamed/removed.
    """

    __tablename__ = "upload_logs"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    platform = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.String(20), nullable=False)
    upload_time = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<UploadLog {self.username} {self.file_name} {self.status}>"
