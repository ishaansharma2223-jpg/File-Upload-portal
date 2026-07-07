"""
utils.py
--------
Shared helper utilities for the FileUploadPortal app, primarily the
login-protection decorators used by the admin and user blueprints.

Two independent session keys are used so that an admin session and a
user session can never be confused with one another:
    session['admin_id']  -> set when an admin logs in
    session['user_id']   -> set when a user logs in
"""

from functools import wraps

from flask import flash, redirect, session, url_for


def admin_required(view_func):
    """
    Decorator that restricts a view to logged-in administrators only.
    Redirects to the admin login page (with a flash message) otherwise.
    """

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as an administrator to continue.", "warning")
            return redirect(url_for("auth.admin_login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def user_required(view_func):
    """
    Decorator that restricts a view to logged-in (and active) users only.
    Redirects to the user login page (with a flash message) otherwise.
    """

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.user_login"))
        return view_func(*args, **kwargs)

    return wrapped_view
