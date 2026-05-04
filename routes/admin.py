"""
Metro Events — Admin Client Approvals
Admins can view and approve pending client registrations here.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from database import db
from models.client_account import ClientAccount

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/client-approvals")
@login_required
def client_approvals():
    """View pending client account approvals."""
    if not current_user.is_admin:
        flash("Access denied. Admins only.", "danger")
        abort(403)
    
    pending = ClientAccount.query.filter_by(
        account_status="pending"
    ).order_by(ClientAccount.created_at.desc()).all()
    
    approved = ClientAccount.query.filter_by(
        account_status="approved"
    ).order_by(ClientAccount.approved_at.desc()).limit(10).all()
    
    return render_template("admin/client_approvals.html",
        pending=pending,
        approved=approved
    )


@admin_bp.route("/client-approvals/<int:account_id>/approve", methods=["POST"])
@login_required
def approve_client_account(account_id):
    """Admin approves a client account."""
    if not current_user.is_admin:
        abort(403)
    
    account = ClientAccount.query.get_or_404(account_id)
    
    if account.account_status != "pending":
        flash("This account is not pending approval.", "warning")
        return redirect(url_for("admin.client_approvals"))
    
    account.approve(approved_by_id=current_user.id)
    db.session.commit()
    
    flash(f"✅ {account.user.email} approved! They can now log in.", "success")
    return redirect(url_for("admin.client_approvals"))


@admin_bp.route("/client-approvals/<int:account_id>/reject", methods=["POST"])
@login_required
def reject_client_account(account_id):
    """Admin rejects a client account."""
    if not current_user.is_admin:
        abort(403)
    
    account = ClientAccount.query.get_or_404(account_id)
    
    if account.account_status != "pending":
        flash("This account is not pending approval.", "warning")
        return redirect(url_for("admin.client_approvals"))
    
    # Delete the rejected account and user
    user = account.user
    db.session.delete(account)
    db.session.delete(user)
    db.session.commit()
    
    flash(f"❌ {user.email} registration rejected and removed.", "success")
    return redirect(url_for("admin.client_approvals"))


@admin_bp.route("/client-approvals/<int:account_id>/suspend", methods=["POST"])
@login_required
def suspend_client_account(account_id):
    """Admin suspends an approved client account."""
    if not current_user.is_admin:
        abort(403)
    
    account = ClientAccount.query.get_or_404(account_id)
    
    account.suspend()
    db.session.commit()
    
    flash(f"⏸️ {account.user.email} account suspended.", "warning")
    return redirect(url_for("admin.client_approvals"))
