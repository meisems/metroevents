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
@login_required # Ensures only logged-in users can reach this
def submit_request():
    package_type = request.form.get("package_type", "Custom")
    client_message = request.form.get("client_message", "").strip()

    # 🟢 THE DUPLICATE BLOCKER
    # We find the existing profile using the logged-in user's email
    email = current_user.email.lower().strip()
    client = Client.query.filter_by(email=email).first()

    if not client:
        # Create profile only if it doesn't exist
        client = Client(
            full_name=current_user.name,
            email=email,
            phone=current_user.phone or "None provided",
            notes=f"Inquiry: {client_message}"
        )
        db.session.add(client)
        db.session.flush() # Generates client.id immediately
    else:
        # Update existing profile notes
        today = datetime.now().strftime("%Y-%m-%d")
        client.notes = (client.notes or "") + f"\n\n[{today}] Requested {package_type}: {client_message}"

    # 🟢 CREATE THE EVENT (With the required Unique ID)
    new_event = Event(
        client_id=client.id,
        name=f"{package_type} Request - {client.full_name}",
        status="new_inquiry"
    )
    
    # CRITICAL: This line generates the "EVT-XXXX" ID your database requires!
    new_event.event_id = Event.generate_unique_id()
    
    db.session.add(new_event)
    
    try:
        db.session.commit()
        flash("⚡ Request sent! Our team will contact you soon.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Something went wrong with the database. Please try again.", "danger")
        print(f"Error: {e}") # This shows up in your Render logs

    return redirect(url_for("public.index"))
