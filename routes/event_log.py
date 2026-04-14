"""
Metro Events — Event Day Log Routes
Handles incidents, notes, change requests, approvals, and sign-offs.
"""

from flask import Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from database import db
from models.event_log import EventLog, LOG_TYPES
from models.event import Event
import os, uuid
from flask import current_app
from werkzeug.utils import secure_filename

event_log_bp = Blueprint("event_log", __name__, url_prefix="/events")

ALLOWED = {"png", "jpg", "jpeg", "gif", "pdf"}


def save_log_photo(file):
    if file and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext in ALLOWED:
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, fname))
            return f"/static/uploads/{fname}"
    return None


# ── Add log entry ─────────────────────────────────────────────────────────

@event_log_bp.route("/<int:event_id>/log/add", methods=["POST"])
@login_required
def add_log(event_id):
    Event.query.get_or_404(event_id)
    photo_file = request.files.get("photo")
    photo_url = save_log_photo(photo_file)

    log = EventLog(
        event_id         = event_id,
        logged_by        = current_user.id,
        log_type         = request.form.get("log_type", "note"),
        message          = request.form.get("message", "").strip(),
        photo_url        = photo_url,
        change_description = request.form.get("change_description", "").strip() or None,
    )
    cost_raw = request.form.get("cost_impact")
    if cost_raw:
        try:
            log.cost_impact = float(cost_raw)
        except ValueError:
            pass

    db.session.add(log)
    db.session.commit()
    flash(f"{log.type_icon} Log entry added.", "success")
    # AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"id": log.id, "message": log.message,
                        "log_type": log.log_type, "logged_at": log.logged_at.isoformat()})
    return redirect(url_for("events.detail", event_id=event_id, tab="event_log"))


# ── Approve change request ────────────────────────────────────────────────

@event_log_bp.route("/<int:event_id>/log/<int:log_id>/approve_change",
                    methods=["POST"])
@login_required
def approve_change(event_id, log_id):
    log = EventLog.query.get_or_404(log_id)
    log.is_approved_by_client = True
    log.approved_by_name = request.form.get("approved_by", "Client")
    db.session.commit()
    flash("Change request approved ✅", "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="event_log"))


# ── Delete log ────────────────────────────────────────────────────────────

@event_log_bp.route("/<int:event_id>/log/<int:log_id>/delete", methods=["POST"])
@login_required
def delete_log(event_id, log_id):
    if not current_user.is_admin:
        flash("Only admins can delete log entries.", "danger")
        return redirect(url_for("events.detail", event_id=event_id, tab="event_log"))
    log = EventLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash("Log entry deleted.", "warning")
    return redirect(url_for("events.detail", event_id=event_id, tab="event_log"))
