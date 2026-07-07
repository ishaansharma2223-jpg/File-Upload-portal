"""
user/routes.py
---------------
All routes available to a logged-in (active) user:
    - Platform Selection
    - Company Selection
    - Upload Screen

Business logic recap:
    The destination folder for an uploaded file is entirely
    ADMIN-CONFIGURED (see FolderPath model). The user only chooses:
        1. Which platform they are working with.
        2. Which company the file belongs to.
        3. Which upload type the file is (Active / Block / Inactive /
           Archive) - this selects WHICH of the four admin-configured
           paths the file is physically saved into.
        4. The source file itself, from their own machine.
"""

import os
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Company, FolderPath, Platform, UploadLog, User
from app.utils import user_required

user_bp = Blueprint("user", __name__)

# The four supported upload types. Order here also drives the dropdown
# order shown to the user on the upload screen.
UPLOAD_TYPES = ["Active", "Block", "Inactive", "Archive"]


def _current_user():
    """Return the User row for the currently logged-in user, or None."""
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


def _companies_for_platform(platform_id, current_user):
    """
    Return the list of companies a user is allowed to pick for a given
    platform.

    Default behaviour: every company that has an admin-configured
    FolderPath for this platform is shown (i.e. only companies the admin
    has actually linked to that platform - not every company in the
    system).

    Restricted behaviour: if the admin has locked this user to a single
    company (User.restricted_company_id), the list is narrowed down to
    just that one company - but only if that company is itself
    configured for this platform. Otherwise the user sees an empty list
    (with a clear message on the page) rather than an unrelated company.
    """
    query = (
        Company.query.join(FolderPath, FolderPath.company_id == Company.id)
        .filter(FolderPath.platform_id == platform_id)
        .order_by(Company.name)
        .distinct()
    )

    if current_user and current_user.restricted_company_id:
        query = query.filter(Company.id == current_user.restricted_company_id)

    return query.all()


@user_bp.route("/platform", methods=["GET", "POST"])
@user_required
def select_platform():
    """Step 1: the user picks which platform they are uploading for."""
    if request.method == "POST":
        platform_id = request.form.get("platform_id")
        platform = Platform.query.get(platform_id)

        if not platform:
            flash("Please select a valid platform.", "danger")
            return redirect(url_for("user.select_platform"))

        # Store the choice in the session so later steps (company
        # selection, upload) know the current context.
        session["selected_platform_id"] = platform.id
        session["selected_platform_name"] = platform.name

        # Changing the platform invalidates any previously selected company.
        session.pop("selected_company_id", None)
        session.pop("selected_company_name", None)

        return redirect(url_for("user.select_company"))

    all_platforms = Platform.query.order_by(Platform.name).all()
    return render_template("user/platform_select.html", platforms=all_platforms)


@user_bp.route("/company", methods=["GET", "POST"])
@user_required
def select_company():
    """
    Step 2: the user picks which company the upload belongs to.

    Only companies that the admin has configured a destination folder
    for (on the currently selected platform) are shown. If the admin has
    restricted this user to a single company, that further narrows the
    list down to just that one company.
    """
    if "selected_platform_id" not in session:
        flash("Please select a platform first.", "warning")
        return redirect(url_for("user.select_platform"))

    current_user = _current_user()
    platform_id = session["selected_platform_id"]
    allowed_companies = _companies_for_platform(platform_id, current_user)
    allowed_company_ids = {company.id for company in allowed_companies}

    if request.method == "POST":
        company_id = request.form.get("company_id")
        # Coerce to int for a safe comparison against the allowed-id set.
        try:
            company_id = int(company_id)
        except (TypeError, ValueError):
            company_id = None

        if company_id not in allowed_company_ids:
            flash("Please select a valid company from the list shown.", "danger")
            return redirect(url_for("user.select_company"))

        company = Company.query.get(company_id)
        session["selected_company_id"] = company.id
        session["selected_company_name"] = company.name
        return redirect(url_for("user.upload"))

    restricted_notice = None
    if current_user and current_user.restricted_company_id and not allowed_companies:
        restricted_notice = (
            "Your account is restricted to a specific company, but that "
            "company has no destination folder configured for this "
            "platform yet. Please contact your administrator."
        )

    return render_template(
        "user/company_select.html",
        companies=allowed_companies,
        restricted_notice=restricted_notice,
    )


@user_bp.route("/upload", methods=["GET", "POST"])
@user_required
def upload():
    """
    Step 3: the user picks an upload type and a source file. The file is
    saved into the admin-configured folder that matches the selected
    platform, company, and upload type, and an UploadLog entry is created
    to record the result.
    """
    if "selected_platform_id" not in session or "selected_company_id" not in session:
        flash("Please select a platform and company before uploading.", "warning")
        return redirect(url_for("user.select_platform"))

    platform_id = session["selected_platform_id"]
    company_id = session["selected_company_id"]

    # Look up the admin-configured destination paths for this combination.
    folder_config = FolderPath.query.filter_by(
        platform_id=platform_id, company_id=company_id
    ).first()

    if request.method == "POST":
        if not folder_config:
            flash(
                "No destination folders have been configured for this "
                "platform/company combination. Please contact the administrator.",
                "danger",
            )
            return redirect(url_for("user.upload"))

        upload_type = request.form.get("upload_type")
        uploaded_file = request.files.get("source_file")

        if upload_type not in UPLOAD_TYPES:
            flash("Please select a valid upload type.", "danger")
            return redirect(url_for("user.upload"))

        if uploaded_file is None or uploaded_file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return redirect(url_for("user.upload"))

        # Sanitize the filename to prevent directory-traversal attacks.
        filename = secure_filename(uploaded_file.filename)
        file_ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "UNKNOWN"

        # The destination folder is entirely admin-configured; the user
        # has no ability to choose or override it.
        destination_dir = folder_config.path_for(upload_type)

        now = datetime.now()
        status = "Success"

        try:
            # Ensure the admin-configured destination directory exists on
            # disk (it may point to a path that hasn't been created yet).
            os.makedirs(destination_dir, exist_ok=True)
            destination_path = os.path.join(destination_dir, filename)
            uploaded_file.save(destination_path)
        except Exception as exc:  # noqa: BLE001 - we want to log any failure reason
            status = f"Failed: {exc}"

        log_entry = UploadLog(
            username=session.get("user_username"),
            platform=session.get("selected_platform_name"),
            company=session.get("selected_company_name"),
            file_name=filename,
            file_type=file_ext,
            status=status,
            upload_date=now.strftime("%Y-%m-%d"),
            upload_time=now.strftime("%H:%M:%S"),
        )
        db.session.add(log_entry)
        db.session.commit()

        if status == "Success":
            flash(f'File "{filename}" was uploaded successfully as {upload_type}.', "success")
        else:
            flash(f"Upload failed: {status}", "danger")

        return redirect(url_for("user.upload"))

    return render_template(
        "user/upload.html",
        folder_config=folder_config,
        upload_types=UPLOAD_TYPES,
    )


@user_bp.route("/change-selection")
@user_required
def change_selection():
    """Allow the user to restart the platform/company selection process."""
    session.pop("selected_platform_id", None)
    session.pop("selected_platform_name", None)
    session.pop("selected_company_id", None)
    session.pop("selected_company_name", None)
    return redirect(url_for("user.select_platform"))
