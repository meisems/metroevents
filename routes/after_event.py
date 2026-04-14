"""
Metro Events — After Event Routes
Post-event feedback capture, photo upload, balance settlement,
and next booking prompt.
"""

from flask import Blueprint, redirect, url_for, flash, request, render_template
from flask_login import login_required, current_user
from database import db
from models.after_event import AfterEvent
from models.event import Event
from datetime import datetime

after_event_bp = Blueprint("after_event", __name__, url_prefix="/events")


def _int_field(form, key):
    raw = form.get(key)
    try:
        return int(raw) if raw else None
    except (ValueError, TypeError):
        return None


@after_event_bp.route("/<int:event_id>/after/save", methods=["POST"])
@login_required
def save_after(event_id):
    event = Event.query.get_or_404(event_id)
    ae = event.after_event or AfterEvent(event_id=event_id)

    ae.client_feedback         = request.form.get("client_feedback", "").strip() or None
    ae.rating_overall          = _int_field(request.form, "rating_overall")
    ae.rating_design           = _int_field(request.form, "rating_design")
    ae.rating_coordination     = _int_field(request.form, "rating_coordination")
    ae.rating_on_time          = _int_field(request.form, "rating_on_time")
    ae.rating_crew             = _int_field(request.form, "rating_crew")
    ae.rating_value            = _int_field(request.form, "rating_value")
    ae.would_recommend         = request.form.get("would_recommend") == "1"
    ae.allow_testimonial       = request.form.get("allow_testimonial") == "1"
    ae.photos_uploaded         = request.form.get("photos_uploaded") == "1"
    ae.final_balance_settled   = request.form.get("final_balance_settled") == "1"
    ae.next_booking_interest   = request.form.get("next_booking_interest") == "1"
    ae.next_event_type         = request.form.get("next_event_type", "").strip() or None
    ae.next_event_notes        = request.form.get("next_event_notes", "").strip() or None
    ae.coordinator_notes       = request.form.get("coordinator_notes", "").strip() or None
    ae.issues_encountered      = request.form.get("issues_encountered", "").strip() or None
    ae.suggestions             = request.form.get("suggestions", "").strip() or None

    raw_settled = request.form.get("balance_settled_date")
    if raw_settled:
        try:
            ae.balance_settled_date = datetime.strptime(raw_settled, "%Y-%m-%d").date()
        except ValueError:
            pass

    if not ae.id:
        db.session.add(ae)

    # Auto-advance event status to 'done' if balance settled
    if ae.final_balance_settled and event.status != "done":
        event.status = "done"

    db.session.commit()
    flash("After-event data saved ✅", "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="after_event"))


@after_event_bp.route("/<int:event_id>/after/prompt_next_booking")
@login_required
def prompt_next_booking(event_id):
    """Redirect to new client inquiry page pre-filled from this event."""
    event = Event.query.get_or_404(event_id)
    return redirect(url_for("clients.detail",
                            client_id=event.client_id,
                            prompt_next="1"))
