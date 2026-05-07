from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from database import db
from models.client import Client
from models.event import Event
from models.review import Review # 👈 Ensure this model exists
from datetime import datetime

public_bp = Blueprint("public", __name__)

# ─── 1. HOME PAGE (INDEX) ──────────────────────────────────────────────────
@public_bp.route("/")
def index():
    # Fetch featured reviews for the testimonials section
    featured_reviews = Review.query.filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(3).all()
    return render_template("landing.html", reviews=featured_reviews)

# ─── 2. SUBMIT REQUEST HANDLER ─────────────────────────────────────────────
@public_bp.route("/submit-request", methods=["POST"])
@login_required
def submit_request():
    phone = request.form.get("phone", "").strip()
    event_date_raw = request.form.get("event_date")
    package_type = request.form.get("package_type", "Custom")
    initial_status = request.form.get("initial_status", "new_inquiry")
    client_message = request.form.get("client_message", "").strip()

    # Find or Create Client
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
        client.phone = phone # Update phone if they changed it
        
    db.session.flush() 

    # Create Event
    try:
        new_event = Event(
            client_id=client.id,
            event_id=Event.generate_unique_id(),
            name=f"{package_type} Request - {client.full_name}",
            event_type=package_type.lower(),
            status=initial_status,
            event_date=datetime.strptime(event_date_raw, "%Y-%m-%d").date() if event_date_raw else datetime.now().date(),
            venue_name="TBD",
            venue_address="TBD",
            total_budget=0.0
        )
        db.session.add(new_event)
        db.session.commit()
        flash("⚡ Request sent! Our team will contact you soon.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"DATABASE ERROR: {e}")
        flash("Error saving request. Please check the details.", "danger")

    return redirect(url_for("public.index"))

# ─── 3. SUBMIT REVIEW HANDLER ──────────────────────────────────────────────
@public_bp.route("/submit-review", methods=["POST"])
@login_required
def submit_review():
    rating = request.form.get("rating", 5, type=int)
    comment = request.form.get("comment", "").strip()

    client = Client.query.filter_by(email=current_user.email).first()
    
    if not client:
        flash("Please submit a request before leaving a review!", "warning")
        return redirect(url_for("public.index"))

    new_review = Review(
        client_id=client.id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(new_review)
    db.session.commit()
    
    flash("🌟 Thank you for your feedback!", "success")
    return redirect(url_for("public.index"))
