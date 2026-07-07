"""
extensions.py
-------------
Houses Flask extension instances that are shared across the application.
Defining them here (separate from app/__init__.py) avoids circular
imports between the application factory and the models/blueprints that
need access to the same extension instances.
"""

from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance used by all models in the project.
db = SQLAlchemy()
