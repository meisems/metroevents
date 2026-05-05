"""
Metro Events — Public Routes
Serves the landing page to visitors and clients.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    # 🚨 THE FIX: Only redirect team members (Admin, Coordinator, Warehouse)
    # Clients are allowed to stay here to see their personalized landing page.
    if current_user.is_authenticated and current_user.role != 'client':
        return redirect(url_for("dashboard.index"))
    
    # Non-logged-in visitors and Clients will see the landing.html
    return render_template("landing.html")
