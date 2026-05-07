"""
Metro Events — Auth Routes
Login, logout, register (public clients & admin team creation), profile, and role promotion.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from database import db
from models.user import User
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # 1. FIXED TRAFFIC DIRECTOR: Only redirect if they are trying to access /login 
    # while already logged in. This prevents the dashboard bouncer loop.
    if current_user.is_authenticated:
        if current_user.role == 'client':
            return redirect("/") 
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
            
            # 2. Check for manual 'next' argument (e.g., from @login_required)
            nxt = request.args.get("next")
            
            # If they are a client, ALWAYS send to root, even if 'next' was dashboard
            if user.role == 'client':
                return redirect("/")
            
            # If they are admin/team, follow 'next' or go to dashboard
            if nxt and not nxt.startswith('/auth'):
                return redirect(nxt)
            return redirect(url_for("dashboard.index"))
            
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
    1. If DB is empty, allow the first user to register as Admin.
    2. If logged in as Admin, allow creating team accounts with specific roles.
    3. If public (not logged in), allow creating a basic 'client' account.
    """
    user_count = User.query.count()

    # Prevent already logged-in non-admins from seeing the register page
    if current_user.is_authenticated and not current_user.is_admin:
        flash("You already have an account.", "info")
        return redirect("/")

    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pwd   = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        
        if user_count == 0:
            role = "admin"
        elif current_user.is_authenticated and current_user.is_admin:
            role = request.form.get("role", "client")
        else:
            role = "client"

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
            elif current_user.is_authenticated and current_user.is_admin:
                flash(f"Team member '{name}' created as {role.title()}.", "success")
                return redirect(url_for("auth.users_list"))
            else:
                flash("Account created successfully! You can now log in.", "success")
                return redirect(url_for("auth.login"))
            
    return render_template("auth/register.html", is_first_user=(user_count == 0))


@auth_bp.route("/users")
@login_required
def users_list():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect("/")
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


@auth_bp.route("/users/<int:user_id>/promote", methods=["POST"])
@login_required
def promote_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect("/")
        
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    
    if user.id == current_user.id and new_role != "admin":
        flash("You cannot demote your own admin account.", "warning")
        return redirect(url_for("auth.users_list"))
        
    valid_roles = ["client", "warehouse", "coordinator", "admin"]
    if new_role in valid_roles:
        user.role = new_role
        db.session.commit()
        flash(f"Account for {user.name} updated to {new_role.title()}.", "success")
    else:
        flash("Invalid role selected.", "danger")
        
    return redirect(url_for("auth.users_list"))

# ─── CHEAT CODE ROUTE ───────────────────────────────────────────────────────

@auth_bp.route("/make-me-admin")
def make_me_admin():
    if current_user.is_authenticated:
        # Securely upgrade the account to admin level
        current_user.role = 'admin'
        db.session.commit()
        return "👑 Success! You are now an Admin. Go back to your dashboard and refresh the page!"
        
    return "You need to log in first! Please log in, then return to this exact URL."
