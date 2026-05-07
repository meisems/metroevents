from flask import Blueprint, render_template, redirect, url_for, flash, request
from database import db
from models.client import Client
from models.event import Event
from datetime import datetime  # 👈 Critical for tracking dates

public_bp = Blueprint("public", __name__)

# ─── HOME PAGE (INDEX) ─────────────────────────────────────────────────────
@public_bp.route("/")
def index():
    # If this route was missing, your whole site would 500/404
    return render_template("public/index.html")

# ─── NEW INQUIRY HANDLER ───────────────────────────────────────────────────
@public_bp.route("/inquiry", methods=["POST"])
def submit_inquiry():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    msg = request.form.get("message", "").strip()
    pkg = request.form.get("package", "Custom")

    if not email:
        flash("Email is required to send an inquiry.", "danger")
        return redirect(url_for("public.index"))

    # 🟢 THE DUPLICATE BLOCKER 🟢
    client = Client.query.filter_by(email=email).first()

    if not client:
        # Create new client
        client = Client(
            full_name=name,
            email=email,
            phone=phone,
            notes=f"PACKAGE REQUEST: {pkg}\nMESSAGE: {msg}"
        )
        db.session.add(client)
        db.session.flush() 
    else:
        # Update existing client notes instead of duplicating
        date_str = datetime.now().strftime("%Y-%m-%d")
        client.notes = (client.notes or "") + f"\n\n--- NEW REQUEST ({date_str}) ---\nPKG: {pkg}\nMSG: {msg}"
        flash(f"Welcome back {name}! We received your new request.", "info")

    # Create the Event
    new_event = Event(
        client_id=client.id,
        name=f"{pkg} Request - {name}",
        status="new_inquiry"
    )
    
    db.session.add(new_event)
    db.session.commit()

    flash("Your inquiry has been sent! We will contact you soon. ✨", "success")
    return redirect(url_for("public.index"))
