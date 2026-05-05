"""
Metro Events — Public Routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from database import db
# Import your inquiry/client model if you plan to save messages
# from models.client import Client 

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    # Only redirect team members to the dashboard
    if current_user.is_authenticated and current_user.role != 'client':
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")

@public_bp.route("/submit-request", methods=["POST"])
@login_required
def submit_request():
    package = request.form.get("package_type")
    message = request.form.get("client_message")
    
    # Logic to save the inquiry would go here
    
    flash(f"Your request for the {package} package has been sent! ⚡", "success")
    return redirect(url_for("public.index"))
