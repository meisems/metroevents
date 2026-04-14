"""
Metro Events — Auth Routes
Login, logout, register (admin only), profile.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from database import db
from models.user import User
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_active and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f"Welcome back, {user.name}! 👋", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard.index"))
            
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Registration Logic:
    1. If DB is empty, allow first user to register as Admin.
    2. If DB has users, require current_user to be Admin.
    """
    user_count = User.query.count()

    # If users exist, enforce security
    if user_count > 0:
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Only admins can create new users.", "danger")
            return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pwd   = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        
        # If first user ever, force 'admin' role, otherwise get from form
        role = "admin" if user_count == 0 else request.form.get("role", "coordinator")

        if User.query.filter_by(email=email).first():
            flash("Email already in use.", "warning")
        else:
            u = User(name=name, email=email, role=role, phone=phone)
            u.set_password(pwd)
            db.session.add(u)
            db.session.commit()
            
            if user_count == 0:
                flash("Admin account created! You can now log in.", "success")
                return redirect(url_for("auth.login"))
            
            flash(f"User {name} created successfully.", "success")
            return redirect(url_for("auth.users_list"))
            
    return render_template("auth/register.html", is_first_user=(user_count == 0))


@auth_bp.route("/users")
@login_required
def users_list():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))
    users = User.query.order_by(User.name).all()
    return render_template("auth/users.html", users=users)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name  = request.form.get("name", current_user.name).strip()
        current_user.phone = request.form.get("phone", "").strip()
        new_pwd = request.form.get("new_password", "")
        if new_pwd:
            current_user.set_password(new_pwd)
        db.session.commit()
        flash("Profile updated.", "success")
    return render_template("auth/profile.html")
