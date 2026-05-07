"""
Metro Events — Clients / CRM Routes
CRUD + pipeline stage management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db
from models.client import Client, PIPELINE_STAGES, PIPELINE_LABELS, NEXT_ACTION
from datetime import datetime

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


def _save_client(client, form):
    client.full_name      = form.get("full_name", "").strip()
    client.email          = form.get("email", "").strip().lower()
    client.phone          = form.get("phone", "").strip()
    client.instagram      = form.get("instagram", "").strip()
    client.address        = form.get("address", "").strip()
    client.referred_by    = form.get("referred_by", "").strip()
    client.notes          = form.get("notes", "").strip()
    client.pipeline_stage = form.get("pipeline_stage", "new_inquiry")
    ocular = form.get("ocular_date")
    if ocular:
        try:
            client.ocular_date = datetime.strptime(ocular, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass


@clients_bp.route("/")
@login_required
def list_clients():
    stage_filter = request.args.get("stage", "")
    search       = request.args.get("q", "").strip()
    page         = request.args.get("page", 1, type=int)

    q = Client.query
    if stage_filter:
        q = q.filter_by(pipeline_stage=stage_filter)
    if search:
        q = q.filter(Client.full_name.ilike(f"%{search}%"))
    clients = q.order_by(Client.created_at.desc()).paginate(page=page, per_page=20)

    stage_counts = {s: Client.query.filter_by(pipeline_stage=s).count()
                    for s in PIPELINE_STAGES}
    return render_template("clients/list.html",
        clients=clients,
        stage_filter=stage_filter,
        search=search,
        stages=PIPELINE_STAGES,
        stage_labels=PIPELINE_LABELS,
        stage_counts=stage_counts,
    )


@clients_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_client():
    if request.method == "POST":
        raw_email = request.form.get("email", "").strip().lower()
        
        # 🟢 FIND OR CREATE LOGIC 🟢
        existing_client = None
        if raw_email:
            # Check if this email already exists in the database
            existing_client = Client.query.filter_by(email=raw_email).first()
            
        if existing_client:
            # Found them! Update their profile instead of duplicating
            _save_client(existing_client, request.form)
            db.session.commit()
            flash(f"Found existing profile for {existing_client.full_name}. Updated their info!", "info")
            return redirect(url_for("clients.detail", client_id=existing_client.id))
        else:
            # Didn't find them! Create a brand new profile
            c = Client()
            _save_client(c, request.form)
            db.session.add(c)
            db.session.commit()
            flash(f"Client {c.full_name} added!", "success")
            return redirect(url_for("clients.detail", client_id=c.id))
            
    return render_template("clients/form.html", client=None,
                           stages=PIPELINE_STAGES, labels=PIPELINE_LABELS)


@clients_bp.route("/<int:client_id>")
@login_required
def detail(client_id):
    client = Client.query.get_or_404(client_id)
    events = client.events.order_by(db.text("event_date desc")).all()
    return render_template("clients/detail.html",
        client=client, events=events,
        stages=PIPELINE_STAGES, labels=PIPELINE_LABELS,
        next_action=NEXT_ACTION,
    )


@clients_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == "POST":
        _save_client(client, request.form)
        db.session.commit()
        flash("Client updated.", "success")
        return redirect(url_for("clients.detail", client_id=client.id))
    return render_template("clients/form.html", client=client,
                           stages=PIPELINE_STAGES, labels=PIPELINE_LABELS)


@clients_bp.route("/<int:client_id>/advance", methods=["POST"])
@login_required
def advance_stage(client_id):
    client = Client.query.get_or_404(client_id)
    client.advance_stage()
    client.last_contacted = datetime.utcnow()
    db.session.commit()
    flash(f"Stage advanced to: {client.stage_label}", "success")
    return redirect(url_for("clients.detail", client_id=client.id))


# ─── DELETE CLIENT (ADMIN ONLY) ───────────────────────────────────────────

@clients_bp.route("/<int:client_id>/delete", methods=["POST"])
@login_required
def delete_client(client_id):
    # Security Check: Kick them out if they aren't an admin
    if not current_user.is_admin:
        flash("Access Denied: Only admins can delete clients.", "danger")
        return redirect(url_for("clients.list_clients"))
        
    from models.client import Client
    
    client = Client.query.get_or_404(client_id)
    client_name = client.full_name
    
    db.session.delete(client)
    db.session.commit()
    
    flash(f"Client '{client_name}' has been permanently deleted.", "warning")
    return redirect(url_for("clients.list_clients"))
