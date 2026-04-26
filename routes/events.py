"""
Metro Events — Events Routes
One Event = One Workspace (tabbed detail view).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from database import db
from models.event import Event, EVENT_TYPES, EVENT_STATUSES
from models.client import Client
from models.user import User
from models.payment import Payment, PAYMENT_TYPES, PAYMENT_STATUSES
from models.moodboard import MoodboardPeg, PEG_CATEGORIES
from models.supplier import Supplier, PurchaseOrder
from datetime import datetime
import os, uuid
from werkzeug.utils import secure_filename

events_bp = Blueprint("events", __name__, url_prefix="/events")

ALLOWED = {"png", "jpg", "jpeg", "gif", "pdf", "docx", "xlsx"}

# ─── HELPERS ───────────────────────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

def save_upload(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        fname = f"{uuid.uuid4().hex}.{ext}"
        folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, fname))
        return f"/static/uploads/{fname}"
    return None

def _populate_event(evt, form):
    evt.name             = form.get("name", "").strip()
    evt.event_type       = form.get("event_type", "wedding")
    evt.status           = form.get("status", "planning")
    evt.venue_name       = form.get("venue_name", "").strip()
    evt.venue_address    = form.get("venue_address", "").strip()
    evt.package_name     = form.get("package_name", "").strip()
    evt.color_palette    = form.get("color_palette", "").strip()
    evt.team_notes       = form.get("team_notes", "").strip()
    evt.internal_notes   = form.get("internal_notes", "").strip()
    evt.total_budget     = float(form.get("total_budget") or 0)

    raw_date = form.get("event_date")
    if raw_date:
        try:
            evt.event_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    for tf in ("event_time_start", "event_time_end", "call_time", "setup_deadline"):
        raw = form.get(tf)
        if raw:
            try:
                setattr(evt, tf, datetime.strptime(raw, "%H:%M").time())
            except ValueError:
                pass

    coord_id = form.get("coordinator_id")
    if coord_id:
        evt.coordinator_id = int(coord_id)

    client_id = form.get("client_id")
    if client_id:
        evt.client_id = int(client_id)


# ─── LIST VIEW ─────────────────────────────────────────────────────────────

@events_bp.route("/")
@login_required
def list_events():
    events = Event.query.order_by(Event.event_date.asc()).all()
    return render_template("events/list.html", events=events, statuses=EVENT_STATUSES)


# ─── CREATE NEW EVENT ──────────────────────────────────────────────────────

@events_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_event():
    if request.method == "POST":
        e = Event()
        _populate_event(e, request.form)

        # Assign the unique ID (e.g., EVT-X4Y7Z9)
        e.event_id = Event.generate_unique_id()

        db.session.add(e)
        db.session.commit()

        flash(f"Event '{e.name}' created with ID {e.event_id}! ⚡", "success")
        return redirect(url_for("events.detail", event_id=e.id))

    clients      = Client.query.order_by(Client.full_name).all()
    coordinators = User.query.filter(User.role.in_(["admin","coordinator"])).all()

    return render_template("events/form.html",
        event=None,
        clients=clients,
        coordinators=coordinators,
        types=EVENT_TYPES,
        statuses=EVENT_STATUSES
    )


# ─── DETAIL (Tabbed Workspace) ─────────────────────────────────────────────

@events_bp.route("/<int:event_id>")
@login_required
def detail(event_id):
    event = Event.query.get_or_404(event_id)
    tab   = request.args.get("tab", "overview")
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.company_name).all()
    all_users = User.query.filter(User.is_active == True).order_by(User.name).all()

    return render_template("events/detail.html",
        event=event,
        tab=tab,
        statuses=EVENT_STATUSES,
        peg_categories=PEG_CATEGORIES,
        payment_types=PAYMENT_TYPES,
        payment_statuses=PAYMENT_STATUSES,
        suppliers=suppliers,
        all_users=all_users,
    )


# ─── QUICK STATUS UPDATE ───────────────────────────────────────────────────

@events_bp.route("/<int:event_id>/update-status", methods=["POST"])
@login_required
def update_status(event_id):
    event = Event.query.get_or_404(event_id)
    new_status = request.form.get("status")

    if new_status in EVENT_STATUSES:
        event.status = new_status
        db.session.commit()
        flash(f"Status for '{event.name}' updated to {new_status.title()}! ✅", "success")
    else:
        flash("Invalid status selected.", "danger")

    return redirect(request.referrer or url_for("events.list_events"))


# ─── EDIT & DELETE ─────────────────────────────────────────────────────────

@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        _populate_event(event, request.form)
        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("events.detail", event_id=event.id))

    clients      = Client.query.order_by(Client.full_name).all()
    coordinators = User.query.filter(User.role.in_(["admin","coordinator"])).all()
    return render_template("events/form.html", event=event,
        clients=clients, coordinators=coordinators,
        types=EVENT_TYPES, statuses=EVENT_STATUSES,
    )

@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id):
    if not current_user.is_admin:
        flash("Only admins can delete events.", "danger")
        return redirect(url_for("events.list_events"))
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "warning")
    return redirect(url_for("events.list_events"))


# ─── PAYMENTS ──────────────────────────────────────────────────────────────

@events_bp.route("/<int:event_id>/payments/add", methods=["POST"])
@login_required
def add_payment(event_id):
    event = Event.query.get_or_404(event_id)
    p = Payment(
        event_id     = event.id,
        payment_type = request.form.get("payment_type", "downpayment"),
        label        = request.form.get("label", "").strip(),
        amount       = float(request.form.get("amount") or 0),
        method       = request.form.get("method", "").strip(),
        reference_number = request.form.get("reference_number", "").strip(),
        notes        = request.form.get("notes", "").strip(),
        status       = request.form.get("status", "pending"),
    )
    raw_due = request.form.get("due_date")
    if raw_due:
        try:
            p.due_date = datetime.strptime(raw_due, "%Y-%m-%d").date()
        except ValueError:
            pass

    proof = request.files.get("proof_file")
    url   = save_upload(proof)
    if url:
        p.proof_of_payment_url = url

    if p.status == "paid":
        p.paid_date = datetime.utcnow().date()

    db.session.add(p)
    db.session.commit()
    flash("Payment recorded.", "success")
    return redirect(url_for("events.detail", event_id=event.id, tab="payments"))


# ─── MOODBOARD & PEGS ──────────────────────────────────────────────────────

@events_bp.route("/<int:event_id>/pegs/add", methods=["POST"])
@login_required
def add_peg(event_id):
    event = Event.query.get_or_404(event_id)
    img_file = request.files.get("peg_image")
    img_url  = save_upload(img_file)

    if not img_url:
        img_url = request.form.get("image_url_ext", "").strip()

    if not img_url:
        flash("Please upload an image or provide a URL.", "warning")
        return redirect(url_for("events.detail", event_id=event_id, tab="moodboard"))

    peg = MoodboardPeg(
        event_id          = event.id,
        title             = request.form.get("title", "").strip(),
        category          = request.form.get("category", "overall_theme"),
        image_url         = img_url,
        source_url        = request.form.get("source_url", "").strip(),
        notes             = request.form.get("notes", "").strip(),
        uploaded_by       = current_user.id,
        is_client_uploaded= False,
    )
    db.session.add(peg)
    db.session.commit()
    flash("Peg added to moodboard!", "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="moodboard"))


# ─── SUPPLIERS & POs ───────────────────────────────────────────────────────

@events_bp.route("/<int:event_id>/po/add", methods=["POST"])
@login_required
def add_po(event_id):
    event = Event.query.get_or_404(event_id)
    proof = request.files.get("proof_file")
    proof_url = save_upload(proof)

    po = PurchaseOrder(
        supplier_id           = int(request.form.get("supplier_id")),
        event_id              = event.id,
        po_number             = request.form.get("po_number", "").strip(),
        description           = request.form.get("description", "").strip(),
        amount                = float(request.form.get("amount") or 0),
        status                = request.form.get("status", "pending"),
        delivery_time_window  = request.form.get("delivery_time_window", "").strip(),
        proof_of_payment_url  = proof_url,
    )

    raw = request.form.get("delivery_date")
    if raw:
        try:
            po.delivery_date = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            pass

    db.session.add(po)
    db.session.commit()
    flash("Purchase order added.", "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="suppliers"))
