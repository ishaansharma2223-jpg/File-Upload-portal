"""
run.py
------
Entry point for running the FileUploadPortal Flask application.

Usage (from the project root, inside your virtual environment):

    python run.py

The application will be available at http://127.0.0.1:5000/

On first run, the database tables are created automatically and a
default administrator account is seeded:

    Username: admin
    Password: admin123

Please change this password immediately after your first login by
adding your own admin-password-change logic, or by editing the
database directly, in any real deployment.
"""

from app import create_app

# Create the Flask application using the application factory pattern.
app = create_app()

if __name__ == "__main__":
    # debug=True enables the interactive debugger and auto-reloader.
    # Set this to False in production environments.
    app.run(debug=True, host="0.0.0.0", port=5000)
