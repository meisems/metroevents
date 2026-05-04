"""
Metro Events — Client Authentication Routes
Self-service registration, login, email verification for clients.
Clients sign up, verify email, await admin approval, then access portal.
"""

import secrets
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request)
from flask_login import login_user, logout_user, login_required, current_user
from database import db
from models.user import User
from models.client import Client
from models.client_account import ClientAccount

client_auth_bp = Blueprint("client_auth", __name__, url_prefix="/client")


def generate_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, token: str):
    """
    TODO: Integrate with your email service (SendGrid, AWS SES, etc.)
    
    For development, log the link to console:
    verification_link = url_for('client_auth.verify_email', token=token, _external=True)
    print(f"📧 Verification link: {verification_link}")
    """
    # Example with Flask-Mail (when implemented):
    # from flask_mail import Message
    # msg = Message(
    #     subject="Verify Your Metro Events Account",
    #     recipients=[email],
    #     body=f"Click here to verify: {verification_link}"
    # )
    # mail.send(msg)
    pass


def send_password_reset_email(email: str, token: str):
    """TODO: Implement email sending for password reset."""
    pass


# ─── REGISTER ──────────────────────────────────────────────────────────────

@client_auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Self-service client registration."""
    if current_user.is_authenticated:
        return redirect(url_for("portal.home"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        
        # ── Validation ─────────────────────────────────────────
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("client_auth.register"))
        
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("client_auth.register"))
        
        if password != password_confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("client_auth.register"))
        
        # ── Check for duplicates ───────────────────────────────
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in or use another email.", "warning")
            return redirect(url_for("client_auth.login"))
        
        # ── Create User account ────────────────────────────────
        user = User(
            name=name,
            email=email,
            role="client",
            phone=phone,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id without committing
        
        # ── Create ClientAccount (pending approval) ────────────
        token = generate_token()
        client_account = ClientAccount(
            user_id=user.id,
            account_status="pending",
            email_verified=False,
            verification_token=token,
            verification_sent_at=datetime.utcnow()
        )
        db.session.add(client_account)
        db.session.commit()
        
        # ── Send verification email ────────────────────────────
        send_verification_email(email, token)
        
        flash("✅ Account created! Please check your email to verify.", "success")
        return redirect(url_for("client_auth.resend_verification"))
    
    return render_template("client/register.html")


# ─── LOGIN ─────────────────────────────────────────────────────────────────

@client_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Client login with status checks."""
    if current_user.is_authenticated:
        return redirect(url_for("portal.home"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("client_auth.login"))
        
        # ── Check role ─────────────────────────────────────────
        if user.role != "client":
            flash("This login is for clients only. Please contact support.", "warning")
            return redirect(url_for("client_auth.login"))
        
        # ── Check ClientAccount status ─────────────────────────
        client_account = ClientAccount.query.filter_by(user_id=user.id).first()
        
        if not client_account:
            flash("Account not found. Please register first.", "danger")
            return redirect(url_for("client_auth.register"))
        
        if not client_account.email_verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("client_auth.resend_verification"))
        
        if client_account.account_status == "pending":
            flash("Your account is pending admin approval. We'll email you soon!", "info")
            return redirect(url_for("client_auth.login"))
        
        if client_account.account_status == "suspended":
            flash("Your account has been suspended. Contact support.", "danger")
            return redirect(url_for("client_auth.login"))
        
        if client_account.account_status != "approved":
            flash("Account status unknown. Contact support.", "danger")
            return redirect(url_for("client_auth.login"))
        
        # ── All checks passed, log in ──────────────────────────
        login_user(user, remember=True)
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash(f"Welcome back, {user.name}! 👋", "success")
        
        nxt = request.args.get("next")
        return redirect(nxt or url_for("portal.home"))
    
    return render_template("client/login.html")


# ─── VERIFY EMAIL ──────────────────────────────────────────────────────────

@client_auth_bp.route("/verify/<token>")
def verify_email(token):
    """Email verification link (one-time use)."""
    client_account = ClientAccount.query.filter_by(
        verification_token=token
    ).first()
    
    if not client_account:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for("client_auth.register"))
    
    if client_account.email_verified:
        flash("Email already verified. Please log in.", "info")
        return redirect(url_for("client_auth.login"))
    
    # ── Mark as verified ───────────────────────────────────────
    client_account.email_verified = True
    client_account.verified_at = datetime.utcnow()
    client_account.verification_token = None  # One-time use
    db.session.commit()
    
    flash("✅ Email verified! Your account is pending admin approval.", "success")
    return redirect(url_for("client_auth.login"))


# ─── RESEND VERIFICATION ──────────────────────────────────────────────────

@client_auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    """Resend verification email if not received."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not found.", "warning")
            return redirect(url_for("client_auth.resend_verification"))
        
        client_account = ClientAccount.query.filter_by(user_id=user.id).first()
        if not client_account:
            flash("Account not found. Please register first.", "danger")
            return redirect(url_for("client_auth.register"))
        
        if client_account.email_verified:
            flash("Email already verified. Please log in.", "info")
            return redirect(url_for("client_auth.login"))
        
        # ── Generate new token ─────────────────────────────────
        token = generate_token()
        client_account.verification_token = token
        client_account.verification_sent_at = datetime.utcnow()
        db.session.commit()
        
        send_verification_email(email, token)
        
        flash("✅ Verification email sent! Check your inbox.", "success")
        return redirect(url_for("client_auth.login"))
    
    return render_template("client/resend_verification.html")


# ─── FORGOT PASSWORD ───────────────────────────────────────────────────────

@client_auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for("portal.home"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        user = User.query.filter_by(email=email).first()
        if user:
            # TODO: Generate reset token and send email
            # token = generate_token()
            # store token in cache or DB with expiry
            # send_password_reset_email(email, token)
            pass
        
        # Always show same message for security (don't reveal if email exists)
        flash("✅ If that email exists, a reset link will be sent shortly.", "success")
        return redirect(url_for("client_auth.login"))
    
    return render_template("client/forgot_password.html")


# ─── LOGOUT ────────────────────────────────────────────────────────────────

@client_auth_bp.route("/logout")
@login_required
def logout():
    """Client logout."""
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("client_auth.login"))
