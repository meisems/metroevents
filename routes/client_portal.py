"""
Metro Events — Client Portal Routes (Phase 2)
Clients log in with role='client' and access their own event:
  - View proposal / quote
  - Approve designs (moodboard pegs)
  - Upload inspiration pegs
  - View payment status
  - Submit after-event feedback
"""

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort)
from flask_login import login_required, current_user
from database import db
from models.event import Event
from models.quote import Quote
from models.payment import Payment
from models.moodboard import MoodboardPeg, PEG_CATEGORIES
from models.after_event import AfterEvent
import os, uuid
from flask import current_app

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")

ALLOWED = {"png", "jpg", "jpeg", "gif", "pdf"}


def client_only(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role != "client":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def save_peg_image(file):
    if file and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext in ALLOWED:
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, fname))
            return f"/static/uploads/{fname}"
    return None


# ─── CLIENT HOME ──────────────────────────────────────────────────────────

@portal_bp.route("/")
@login_required
@client_only
def home():
    """Show client's events."""
    # Find events where client email matches user email
    from models.client import Client
    client = Client.query.filter_by(email=current_user.email).first()
    events = client.events.order_by(Event.event_date.desc()).all() if client else []
    return render_template("portal/home.html", client=client, events=events)


# ─── EVENT OVERVIEW ───────────────────────────────────────────────────────

@portal_bp.route("/event/<int:event_id>")
@login_required
@client_only
def event_overview(event_id):
    event = _get_client_event(event_id)
    quote = event.active_quote
    payments = event.payments.order_by(Payment.due_date).all()
    pegs = event.moodboard_pegs.order_by(MoodboardPeg.created_at.desc()).all()
    return render_template("portal/event.html",
        event=event, quote=quote, payments=payments, pegs=pegs,
        peg_categories=PEG_CATEGORIES,
    )


# ─── APPROVE QUOTE ────────────────────────────────────────────────────────

@portal_bp.route("/event/<int:event_id>/approve_quote/<int:quote_id>",
                 methods=["POST"])
@login_required
@client_only
def approve_quote(event_id, quote_id):
    event = _get_client_event(event_id)
    quote = Quote.query.get_or_404(quote_id)
    if quote.event_id != event.id:
        abort(403)
    quote.approve(by_name=current_user.name)
    db.session.commit()
    flash("✅ Quote approved! Our team will be in touch.", "success")
    return redirect(url_for("portal.event_overview", event_id=event_id))


# ─── APPROVE PEG ──────────────────────────────────────────────────────────

@portal_bp.route("/event/<int:event_id>/pegs/<int:peg_id>/approve",
                 methods=["POST"])
@login_required
@client_only
def approve_peg(event_id, peg_id):
    event = _get_client_event(event_id)
    peg = MoodboardPeg.query.get_or_404(peg_id)
    if peg.event_id != event.id:
        abort(403)
    peg.approve()
    db.session.commit()
    flash("✅ Design approved!", "success")
    return redirect(url_for("portal.event_overview", event_id=event_id))


# ─── UPLOAD PEG ───────────────────────────────────────────────────────────

@portal_bp.route("/event/<int:event_id>/pegs/upload", methods=["POST"])
@login_required
@client_only
def upload_peg(event_id):
    event = _get_client_event(event_id)
    img_url = save_peg_image(request.files.get("peg_image"))
    if not img_url:
        img_url = request.form.get("image_url_ext", "").strip()
    if not img_url:
        flash("Please upload an image or provide a URL.", "warning")
        return redirect(url_for("portal.event_overview", event_id=event_id))
    peg = MoodboardPeg(
        event_id           = event.id,
        title              = request.form.get("title", "").strip(),
        category           = request.form.get("category", "client_uploaded"),
        image_url          = img_url,
        source_url         = request.form.get("source_url", "").strip(),
        notes              = request.form.get("notes", "").strip(),
        uploaded_by        = current_user.id,
        is_client_uploaded = True,
    )
    db.session.add(peg)
    db.session.commit()
    flash("Inspiration peg uploaded! ✨ Our team will review it.", "success")
    return redirect(url_for("portal.event_overview", event_id=event_id))


# ─── CLIENT FEEDBACK ──────────────────────────────────────────────────────

@portal_bp.route("/event/<int:event_id>/feedback", methods=["GET", "POST"])
@login_required
@client_only
def submit_feedback(event_id):
    event = _get_client_event(event_id)
    ae = event.after_event or AfterEvent(event_id=event_id)

    if request.method == "POST":
        def _int(key):
            raw = request.form.get(key)
            try: return int(raw) if raw else None
            except: return None

        ae.client_feedback       = request.form.get("client_feedback", "").strip()
        ae.rating_overall        = _int("rating_overall")
        ae.rating_design         = _int("rating_design")
        ae.rating_coordination   = _int("rating_coordination")
        ae.rating_on_time        = _int("rating_on_time")
        ae.rating_crew           = _int("rating_crew")
        ae.rating_value          = _int("rating_value")
        ae.would_recommend       = request.form.get("would_recommend") == "1"
        ae.allow_testimonial     = request.form.get("allow_testimonial") == "1"
        ae.next_booking_interest = request.form.get("next_booking_interest") == "1"
        ae.next_event_type       = request.form.get("next_event_type", "").strip() or None
        ae.submitted_by_client   = True

        if not ae.id:
            db.session.add(ae)
        db.session.commit()
        flash("💛 Salamat sa inyong feedback! We appreciate it.", "success")
        return redirect(url_for("portal.event_overview", event_id=event_id))

    return render_template("portal/feedback.html", event=event, ae=ae)


# ─── HELPER ───────────────────────────────────────────────────────────────

def _get_client_event(event_id: int) -> Event:
    """Return event only if it belongs to the logged-in client's email."""
    from models.client import Client
    event = Event.query.get_or_404(event_id)
    client = Client.query.filter_by(email=current_user.email).first()
    if not client or event.client_id != client.id:
        abort(403)
    return event
