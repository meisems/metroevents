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
    # 1. Capture Form Data
    package_type = request.form.get("package_type", "Custom")
    client_message = request.form.get("client_message", "").strip()

    # 🟢 THE DUPLICATE BLOCKER: Find or Create Client
    email = current_user.email.lower().strip()
    client = Client.query.filter_by(email=email).first()

    if not client:
        # Create profile only if it doesn't exist
        client = Client(
            full_name=current_user.name,
            email=email,
            phone=current_user.phone or "Not Provided",
            pipeline_stage="new_inquiry" # Set initial stage to satisfy DB
        )
        db.session.add(client)
        db.session.flush() # Generates client.id immediately for the event link
    else:
        # Update existing profile notes with the new timestamped inquiry
        today = datetime.now().strftime("%Y-%m-%d")
        client.notes = (client.notes or "") + f"\n\n[{today}] Inquiry: {client_message}"

    # 🟢 CREATE THE EVENT: Satisfying all Database Constraints
    try:
        new_event = Event(
            client_id=client.id,
            event_id=Event.generate_unique_id(), # Generates EVT-XXXX
            name=f"{package_type} Request - {client.full_name}",
            
            # --- MANDATORY FIELDS ---
            # Most databases require these to be non-null. 
            # We map the package type to event_type.
            event_type=package_type.lower(), 
            status="planning", 
            total_budget=0.0, # Default to 0.0 to avoid Math/Null errors later
            team_notes=f"Client Message: {client_message}"
        )
        
        db.session.add(new_event)
        db.session.commit()
        flash("⚡ Request sent! Our team will review your vision and contact you soon.", "success")
        
    except Exception as e:
        db.session.rollback()
        # This will show you exactly what field is missing in your Render Logs
        print(f"CRITICAL DATABASE ERROR: {str(e)}") 
        flash("We couldn't save your request. Please try again or contact support.", "danger")

    return redirect(url_for("public.index"))
