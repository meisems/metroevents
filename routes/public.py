from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from database import db
from models.client import Client
from models.event import Event
from datetime import datetime

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    return render_template("landing.html")

@public_bp.route("/submit-request", methods=["POST"])
@login_required
def submit_request():
    package_type = request.form.get("package_type", "Custom")
    client_message = request.form.get("client_message", "").strip()

    # 🟢 1. Find or Create Client (The Duplicate Blocker)
    email = current_user.email.lower().strip()
    client = Client.query.filter_by(email=email).first()

    if not client:
        client = Client(
            full_name=current_user.name,
            email=email,
            phone=current_user.phone or "Not Provided",
            pipeline_stage="new_inquiry"
        )
        db.session.add(client)
        db.session.flush() 
    else:
        # Update notes for existing client
        today_str = datetime.now().strftime("%Y-%m-%d")
        client.notes = (client.notes or "") + f"\n\n[{today_str}] New Inquiry: {client_message}"

    # 🟢 2. Create the Event (Fixing the 'NotNullViolation' error)
    try:
        new_event = Event(
            client_id=client.id,
            event_id=Event.generate_unique_id(),
            name=f"{package_type} Request - {client.full_name}",
            event_type=package_type.lower(),
            status="planning",
            
            # ✅ THE FIX: We provide a default date to satisfy the NOT NULL constraint.
            # You can change this to the actual intended date later in the Admin dashboard.
            event_date=datetime.now().date(), 
            
            # Also providing defaults for other potentially strict columns
            venue_name="TBD (Inquiry Phase)",
            venue_address="TBD (Inquiry Phase)",
            total_budget=0.0,
            team_notes=f"Initial Inquiry: {client_message}"
        )
        
        db.session.add(new_event)
        db.session.commit()
        flash("⚡ Request sent! Our team will contact you soon.", "success")
        
    except Exception as e:
        db.session.rollback()
        # This will now print any NEW missing fields to your Render logs
        print(f"CRITICAL DATABASE ERROR: {str(e)}") 
        flash("We encountered a database error. Our team has been notified.", "danger")

    return redirect(url_for("public.index"))
