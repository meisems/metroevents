from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from database import db
from models.client import Client
from models.event import Event
from datetime import datetime

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    # 🚨 IMPORTANT: Make sure your HTML file is named landing.html 
    # and is located directly in the /templates folder.
    return render_template("landing.html")

@public_bp.route("/submit-request", methods=["POST"])
def submit_request():
    package_type = request.form.get("package_type")
    client_message = request.form.get("client_message", "").strip()

    if not current_user.is_authenticated:
        flash("Please log in to submit a request.", "warning")
        return redirect(url_for("auth.login"))

    # 🟢 THE DUPLICATE BLOCKER
    # This logic checks if the email already exists before creating a new row
    email = current_user.email.lower().strip()
    client = Client.query.filter_by(email=email).first()

    if not client:
        # Create a new profile only if one doesn't exist
        client = Client(
            full_name=current_user.name,
            email=email,
            phone=current_user.phone or "None",
            notes=f"Initial Inquiry: {client_message}"
        )
        db.session.add(client)
        db.session.flush() 
    else:
        # If they exist, just update their notes instead of making a new row
        today = datetime.now().strftime("%Y-%m-%d")
        client.notes = (client.notes or "") + f"\n\n[{today}] New Request: {package_type}\n{client_message}"

    # Create the Event and attach it to the (existing or new) client
    new_event = Event(
        client_id=client.id,
        name=f"{package_type} Request - {client.full_name}",
        status="new_inquiry"
    )
    
    db.session.add(new_event)
    db.session.commit()

    flash("⚡ Request submitted! Check your CRM to see it in the folder.", "success")
    return redirect(url_for("public.index"))
