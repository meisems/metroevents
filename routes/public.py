from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from database import db
from models.client import Client
from models.event import Event
from models.review import Review
from datetime import datetime

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    return render_template("landing.html")

@public_bp.route("/submit-request", methods=["POST"])
@login_required
def submit_request():
    # 1. Capture All Form Data
    phone = request.form.get("phone", "").strip()
    event_date_raw = request.form.get("event_date")
    package_type = request.form.get("package_type", "Custom")
    initial_status = request.form.get("initial_status", "new_inquiry")
    client_message = request.form.get("client_message", "").strip()

    # 🟢 STEP 1: Find or Create/Update Client
    email = current_user.email.lower().strip()
    client = Client.query.filter_by(email=email).first()

    if not client:
        client = Client(
            full_name=current_user.name,
            email=email,
            phone=phone,
            pipeline_stage="new_inquiry"
        )
        db.session.add(client)
    else:
        # Update existing contact info if they provided a new phone
        client.phone = phone
        today = datetime.now().strftime("%Y-%m-%d")
        client.notes = (client.notes or "") + f"\n\n[{today}] New Request ({initial_status}): {client_message}"

    db.session.flush() # Secure the client ID

    # 🟢 STEP 2: Create the Event with the filled information
    try:
        new_event = Event(
            client_id=client.id,
            event_id=Event.generate_unique_id(),
            name=f"{package_type} Request - {client.full_name}",
            event_type=package_type.lower(),
            status=initial_status, # Saves the status chosen by the client
            team_notes=f"CLIENT MESSAGE: {client_message}",
            total_budget=0.0
        )

        # Convert the date string to a Python date object
        if event_date_raw:
            new_event.event_date = datetime.strptime(event_date_raw, "%Y-%m-%d").date()

        db.session.add(new_event)
        db.session.commit()
        flash("⚡ Thank you! Your request has been received and our team will contact you.", "success")
        
    except Exception as e:
        db.session.rollback()
        print(f"SUBMISSION ERROR: {str(e)}")
        flash("Error saving your request. Please check the date format.", "danger")

    return redirect(url_for("public.index"))

@public_bp.route("/")
def index():
    # Only show "Featured" reviews on the landing page
    featured_reviews = Review.query.filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(3).all()
    return render_template("landing.html", reviews=featured_reviews)

@public_bp.route("/submit-review", methods=["POST"])
@login_required
def submit_review():
    rating = request.form.get("rating", 5, type=int)
    comment = request.form.get("comment", "").strip()

    # Find the client profile linked to this user
    client = Client.query.filter_by(email=current_user.email).first()
    
    if not client:
        flash("You need a client profile to leave a review. Please submit a request first!", "warning")
        return redirect(url_for("public.index"))

    new_review = Review(
        client_id=client.id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(new_review)
    db.session.commit()
    
    flash("🌟 Thank you for your feedback! It means the world to us.", "success")
    return redirect(url_for("public.index"))
