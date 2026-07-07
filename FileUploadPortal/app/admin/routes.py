"""
admin/routes.py
----------------
All routes available to a logged-in administrator:
    - Dashboard (summary statistics + recent uploads)
    - User Management (create, activate/deactivate, delete users)
    - Platform Management (create/delete platforms)
    - Company Management (create/delete companies)
    - Destination Folder Management (configure the four physical paths
      that uploaded files are routed into, per platform/company pair)
    - Upload Logs (browse and filter the upload audit trail)
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Company, FolderPath, Platform, UploadLog, User
from app.utils import admin_required

admin_bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Show high-level counts and the most recent upload activity."""
    stats = {
        "users": User.query.count(),
        "platforms": Platform.query.count(),
        "companies": Company.query.count(),
        "folders": FolderPath.query.count(),
        "logs": UploadLog.query.count(),
    }
    recent_logs = UploadLog.query.order_by(UploadLog.id.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, recent_logs=recent_logs)


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------
@admin_bp.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    """List all users and handle creation of new user accounts."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # Empty string / "0" means "All Companies" (no restriction).
        restricted_company_id = request.form.get("restricted_company_id") or None

        if not username or not password:
            flash("Username and password are both required.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "danger")
        else:
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                restricted_company_id=restricted_company_id,
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'User "{username}" was created successfully.', "success")
        return redirect(url_for("admin.users"))

    all_users = User.query.order_by(User.id.desc()).all()
    all_companies = Company.query.order_by(Company.name).all()
    return render_template("admin/users.html", users=all_users, companies=all_companies)


@admin_bp.route("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    """Flip a user's active/inactive status (used to block logins)."""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    state = "activated" if user.is_active else "deactivated"
    flash(f'User "{user.username}" has been {state}.', "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/set-company-access", methods=["POST"])
@admin_required
def set_company_access(user_id):
    """
    Restrict (or un-restrict) which single company a user is allowed to
    see/select. Leaving the selection empty restores default behaviour,
    where the user can access every company configured for whichever
    platform they pick.
    """
    user = User.query.get_or_404(user_id)
    restricted_company_id = request.form.get("restricted_company_id") or None
    user.restricted_company_id = restricted_company_id
    db.session.commit()

    if user.restricted_company_id:
        flash(
            f'User "{user.username}" is now restricted to company '
            f'"{user.restricted_company.name}".',
            "info",
        )
    else:
        flash(f'User "{user.username}" can now access all companies again.', "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id):
    """Permanently delete a user account."""
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" was deleted.', "info")
    return redirect(url_for("admin.users"))



# ---------------------------------------------------------------------------
# Platform Management
# ---------------------------------------------------------------------------
@admin_bp.route("/platforms", methods=["GET", "POST"])
@admin_required
def platforms():
    """List all platforms and handle creation of new platforms."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("Platform name is required.", "danger")
        elif Platform.query.filter_by(name=name).first():
            flash("That platform already exists.", "danger")
        else:
            db.session.add(Platform(name=name))
            db.session.commit()
            flash(f'Platform "{name}" was added.', "success")
        return redirect(url_for("admin.platforms"))

    all_platforms = Platform.query.order_by(Platform.name).all()
    return render_template("admin/platforms.html", platforms=all_platforms)


@admin_bp.route("/platforms/<int:platform_id>/delete")
@admin_required
def delete_platform(platform_id):
    """Delete a platform. Cascades to remove its folder configurations."""
    platform = Platform.query.get_or_404(platform_id)
    name = platform.name
    db.session.delete(platform)
    db.session.commit()
    flash(f'Platform "{name}" was deleted.', "info")
    return redirect(url_for("admin.platforms"))


# ---------------------------------------------------------------------------
# Company Management
# ---------------------------------------------------------------------------
@admin_bp.route("/companies", methods=["GET", "POST"])
@admin_required
def companies():
    """List all companies and handle creation of new companies."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("Company name is required.", "danger")
        elif Company.query.filter_by(name=name).first():
            flash("That company already exists.", "danger")
        else:
            db.session.add(Company(name=name))
            db.session.commit()
            flash(f'Company "{name}" was added.', "success")
        return redirect(url_for("admin.companies"))

    all_companies = Company.query.order_by(Company.name).all()
    return render_template("admin/companies.html", companies=all_companies)


@admin_bp.route("/companies/<int:company_id>/delete")
@admin_required
def delete_company(company_id):
    """Delete a company. Cascades to remove its folder configurations."""
    company = Company.query.get_or_404(company_id)
    name = company.name
    db.session.delete(company)
    db.session.commit()
    flash(f'Company "{name}" was deleted.', "info")
    return redirect(url_for("admin.companies"))


# ---------------------------------------------------------------------------
# Destination Folder Management
# ---------------------------------------------------------------------------
@admin_bp.route("/folders", methods=["GET", "POST"])
@admin_required
def folders():
    """
    List all folder-path configurations and handle creation/update of a
    configuration for a given (platform, company) pair. If a configuration
    already exists for the chosen pair, it is updated in place instead of
    creating a duplicate row (the database also enforces this uniqueness).
    """
    if request.method == "POST":
        platform_id = request.form.get("platform_id")
        company_id = request.form.get("company_id")
        active_path = request.form.get("active_path", "").strip()
        block_path = request.form.get("block_path", "").strip()
        inactive_path = request.form.get("inactive_path", "").strip()
        archive_path = request.form.get("archive_path", "").strip()

        if not all([platform_id, company_id, active_path, block_path, inactive_path, archive_path]):
            flash("Platform, company, and all four destination paths are required.", "danger")
            return redirect(url_for("admin.folders"))

        existing = FolderPath.query.filter_by(
            platform_id=platform_id, company_id=company_id
        ).first()

        if existing:
            existing.active_path = active_path
            existing.block_path = block_path
            existing.inactive_path = inactive_path
            existing.archive_path = archive_path
            flash("Folder configuration was updated.", "success")
        else:
            db.session.add(
                FolderPath(
                    platform_id=platform_id,
                    company_id=company_id,
                    active_path=active_path,
                    block_path=block_path,
                    inactive_path=inactive_path,
                    archive_path=archive_path,
                )
            )
            flash("Folder configuration was added.", "success")

        db.session.commit()
        return redirect(url_for("admin.folders"))

    all_folders = FolderPath.query.all()
    all_platforms = Platform.query.order_by(Platform.name).all()
    all_companies = Company.query.order_by(Company.name).all()
    return render_template(
        "admin/folders.html",
        folders=all_folders,
        platforms=all_platforms,
        companies=all_companies,
    )


@admin_bp.route("/folders/<int:folder_id>/delete")
@admin_required
def delete_folder(folder_id):
    """Delete a destination-folder configuration."""
    folder = FolderPath.query.get_or_404(folder_id)
    db.session.delete(folder)
    db.session.commit()
    flash("Folder configuration was deleted.", "info")
    return redirect(url_for("admin.folders"))


# ---------------------------------------------------------------------------
# Upload Logs
# ---------------------------------------------------------------------------
@admin_bp.route("/logs")
@admin_required
def logs():
    """Browse the upload audit trail, optionally filtered by username/status."""
    query = UploadLog.query

    username_filter = request.args.get("username", "").strip()
    status_filter = request.args.get("status", "").strip()

    if username_filter:
        query = query.filter(UploadLog.username.ilike(f"%{username_filter}%"))
    if status_filter:
        query = query.filter(UploadLog.status == status_filter)

    all_logs = query.order_by(UploadLog.id.desc()).all()
    return render_template(
        "admin/logs.html",
        logs=all_logs,
        username_filter=username_filter,
        status_filter=status_filter,
    )
