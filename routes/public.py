"""
Metro Events — Public Routes
Serves the landing page to non-logged-in visitors.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def landing():
    # If already logged in, go straight to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")
