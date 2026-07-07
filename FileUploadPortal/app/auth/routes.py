"""
auth/routes.py
--------------
Routes shared by both admin and user authentication flows:
    - Landing page that lets a visitor choose which portal to log into.
    - Admin login.
    - User login (with an active/inactive account check).
    - A single logout route that clears whichever session is active.
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.models import Admin, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Landing page: lets the visitor pick the admin or user portal."""
    return render_template("index.html")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Authenticate an administrator and start an admin session."""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password_hash, password):
            # Clear any previous session data (e.g. a stale user session)
            # before establishing the new admin session.
            session.clear()
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash(f"Welcome back, {admin.username}!", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid admin username or password.", "danger")

    return render_template("auth/admin_login.html")


@auth_bp.route("/user/login", methods=["GET", "POST"])
def user_login():
    """Authenticate a regular user and start a user session."""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "danger")
        elif not user.is_active:
            flash("Your account has been deactivated. Please contact the administrator.", "danger")
        else:
            session.clear()
            session["user_id"] = user.id
            session["user_username"] = user.username
            flash(f"Welcome, {user.username}!", "success")
            return redirect(url_for("user.select_platform"))

    return render_template("auth/user_login.html")


@auth_bp.route("/logout")
def logout():
    """Clear the session (works for both admin and user sessions) and log out."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.index"))
