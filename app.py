"""
Metro Events — Application Factory
Creates and configures the Flask app. Run with: python run.py
"""

import os
from flask import Flask
from config import config
from database import db, login_manager, migrate, csrf


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ── Ensure upload folder exists ───────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Initialize extensions ─────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ── Register blueprints ───────────────────────────────────
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.clients import clients_bp
    from routes.events import events_bp
    from routes.quotes import quotes_bp
    from routes.inventory import inventory_bp
    from routes.tasks import tasks_bp
    from routes.checklist import checklist_bp
    from routes.event_log import event_log_bp
    # ── NEW: Phase 2 blueprints ───────────────────────────────
    from routes.suppliers import suppliers_bp
    from routes.reports import reports_bp
    from routes.after_event import after_event_bp
    from routes.files import files_bp
    from routes.reminders import reminders_bp
    from routes.client_portal import portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(event_log_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(after_event_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(portal_bp)

    # ── Jinja2 global helpers ─────────────────────────────────
    @app.template_filter("peso")
    def peso_filter(value):
        try:
            return f"₱{float(value):,.2f}"
        except (TypeError, ValueError):
            return "₱0.00"

    @app.template_filter("dateformat")
    def date_filter(value, fmt="%b %d, %Y"):
        if not value:
            return "—"
        if hasattr(value, "strftime"):
            return value.strftime(fmt)
        return str(value)

    @app.template_filter("stars")
    def stars_filter(value):
        """Render star rating as unicode stars."""
        try:
            r = int(value or 0)
            return "★" * r + "☆" * (5 - r)
        except (TypeError, ValueError):
            return "☆☆☆☆☆"

    @app.context_processor
    def inject_globals():
        from datetime import date, timedelta
        from models.payment import Payment
        from models.event import Event
        today = date.today()
        in_3 = today + timedelta(days=3)
        overdue_count = (Payment.query
                         .filter(Payment.status == "pending",
                                 Payment.due_date < today)
                         .count())
        due_soon_count = (Payment.query
                          .filter(Payment.status == "pending",
                                  Payment.due_date >= today,
                                  Payment.due_date <= in_3)
                          .count())
        return {
            "APP_NAME":       app.config["APP_NAME"],
            "APP_TAGLINE":    app.config["APP_TAGLINE"],
            "overdue_count":  overdue_count,
            "due_soon_count": due_soon_count,
        }

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    return app
