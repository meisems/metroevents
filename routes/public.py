"""
Metro Events — Public Routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from database import db

# The name 'public' here must match what you use in url_for('public.index')
public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    # Only redirect team members. Clients stay on the landing page.
    if current_user.is_authenticated and current_user.role != 'client':
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")

@public_bp.route("/submit-request", methods=["POST"])
@login_required
def submit_request():
    package = request.form.get("package_type")
    message = request.form.get("client_message")
    
    # ── SAVE TO DATABASE ──────────────────────────────────────
    from models.client import Client  # Import your Client model
    
    # Create a new entry in your CRM
    new_inquiry = Client(
        full_name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        pipeline_stage="new_inquiry", # This matches your dashboard filter
        notes=f"PACKAGE REQUEST: {package}\n\nMESSAGE: {message}"
    )
    
    db.session.add(new_inquiry)
    db.session.commit()
    # ──────────────────────────────────────────────────────────
    
    flash(f"Your request for the {package} package has been sent to our team! ⚡", "success")
    return redirect(url_for("public.index"))
