"""
Metro Events — Checklist Routes
Pre-prod, fabrication, supplier, load-in/out checklists per event.
Supports template loading, CRUD, and tick/untick actions.
"""

from flask import Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from database import db
from models.checklist import ChecklistItem, CHECKLIST_PHASES, apply_template
from models.event import Event
from datetime import datetime

checklist_bp = Blueprint("checklist", __name__, url_prefix="/events")


# ── Add item ──────────────────────────────────────────────────────────────

@checklist_bp.route("/<int:event_id>/checklist/add", methods=["POST"])
@login_required
def add_item(event_id):
    Event.query.get_or_404(event_id)
    raw_due = request.form.get("due_date")
    item = ChecklistItem(
        event_id         = event_id,
        phase            = request.form.get("phase", "pre_production"),
        title            = request.form.get("title", "").strip(),
        description      = request.form.get("description", "").strip(),
        responsible_role = request.form.get("responsible_role", "").strip(),
        sort_order       = int(request.form.get("sort_order") or 0),
    )
    if raw_due:
        try:
            item.due_date = datetime.strptime(raw_due, "%Y-%m-%d").date()
        except ValueError:
            pass
    db.session.add(item)
    db.session.commit()
    flash("Checklist item added.", "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="checklist"))


# ── Load template ─────────────────────────────────────────────────────────

@checklist_bp.route("/<int:event_id>/checklist/load_template", methods=["POST"])
@login_required
def load_template(event_id):
    if not current_user.is_admin and not current_user.is_coordinator:
        flash("Access denied.", "danger")
        return redirect(url_for("events.detail", event_id=event_id, tab="checklist"))
    event = Event.query.get_or_404(event_id)
    template_key = request.form.get("template_key", event.event_type)
    # clear existing if requested
    if request.form.get("clear_existing") == "1":
        ChecklistItem.query.filter_by(event_id=event_id).delete()
    items = apply_template(event, template_key)
    for it in items:
        db.session.add(it)
    db.session.commit()
    flash(f"'{template_key.title()}' checklist template loaded ({len(items)} items).",
          "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="checklist"))


# ── Tick / Untick ─────────────────────────────────────────────────────────

@checklist_bp.route("/<int:event_id>/checklist/<int:item_id>/tick", methods=["POST"])
@login_required
def tick_item(event_id, item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    if item.is_done:
        item.untick()
        msg = "Item marked incomplete."
        color = "info"
    else:
        item.tick(current_user.name)
        msg = "✅ Item ticked off!"
        color = "success"
    db.session.commit()
    # AJAX-friendly: return JSON if requested
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"done": item.is_done, "done_by": item.done_by})
    flash(msg, color)
    return redirect(url_for("events.detail", event_id=event_id, tab="checklist"))


# ── Update notes ──────────────────────────────────────────────────────────

@checklist_bp.route("/<int:event_id>/checklist/<int:item_id>/notes", methods=["POST"])
@login_required
def update_notes(event_id, item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    item.notes = request.form.get("notes", "").strip()
    db.session.commit()
    flash("Notes saved.", "info")
    return redirect(url_for("events.detail", event_id=event_id, tab="checklist"))


# ── Delete ────────────────────────────────────────────────────────────────

@checklist_bp.route("/<int:event_id>/checklist/<int:item_id>/delete",
                    methods=["POST"])
@login_required
def delete_item(event_id, item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item removed.", "warning")
    return redirect(url_for("events.detail", event_id=event_id, tab="checklist"))
