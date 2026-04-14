"""
Metro Events — Database & Extensions
Single place to initialize Flask extensions so we avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# ── Extensions (initialized without app — bound later via init_app) ────────
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

# ── Login manager config ───────────────────────────────────────────────────
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access Metro Events."
login_manager.login_message_category = "warning"
