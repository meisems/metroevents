"""
Metro Events — Dashboard Route
Aggregates KPIs, upcoming events, overdue tasks & payments.
"""
from flask import Blueprint, render_template, redirect, flash, url_for
from flask_login import login_required, current_user
from database import db
from models.event import Event
from models.client import Client
from models.task import Task
from models.payment import Payment
from models.inventory import InventoryItem
from models.review import Review
from datetime import datetime, date, timedelta

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/reviews")
@login_required
def manage_reviews():
    if current_user.role == 'client':
        return redirect(url_for('public.index'))
        
    # Get all reviews, newest first
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=all_reviews)

@dashboard_bp.route("/reviews/<int:review_id>/toggle-feature", methods=["POST"])
@login_required
def toggle_review_feature(review_id):
    if current_user.role == 'client': abort(403)
    
    review = Review.query.get_or_404(review_id)
    review.is_featured = not review.is_featured # Fills the checkbox logic
    db.session.commit()
    
    status = "featured" if review.is_featured else "removed from featured"
    flash(f"Review by {review.client.full_name} is now {status}.", "success")
    return redirect(url_for('dashboard.manage_reviews'))

@dashboard_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    if current_user.role != 'admin': abort(403)
    
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted permanently.", "warning")
    return redirect(url_for('dashboard.manage_reviews'))

@dashboard_bp.route("/dashboard")
@login_required
def index():
    if current_user.role == 'client':
        flash("Welcome to your portal!", "info")
        # Ensure this is 'public.index'
        return redirect(url_for('public.index')) 
    
    # ... rest of your code

    # ... rest of your dashboard code ...

    today = date.today()
    upcoming_days = today + timedelta(days=30)

    # ── KPI counts ────────────────────────────────────────────
    total_events   = Event.query.count()
    active_events  = Event.query.filter(
        Event.status.in_(["planning", "production", "ready", "event_day"])
    ).count()
    total_clients  = Client.query.count()
    new_inquiries  = Client.query.filter_by(pipeline_stage="new_inquiry").count()

    # ── Upcoming events (next 30 days) ────────────────────────
    upcoming = (Event.query
                .filter(Event.event_date >= today,
                        Event.event_date <= upcoming_days,
                        Event.status != "cancelled")
                .order_by(Event.event_date)
                .limit(8).all())

    # ── Overdue tasks ─────────────────────────────────────────
    overdue_tasks = (Task.query
                     .filter(Task.is_done == False,
                             Task.due_date < today)
                     .order_by(Task.due_date)
                     .limit(8).all())

    # ── Overdue payments ──────────────────────────────────────
    overdue_payments = (Payment.query
                        .filter(Payment.status == "pending",
                                Payment.due_date < today)
                        .order_by(Payment.due_date)
                        .limit(6).all())

    # ── Recent clients ────────────────────────────────────────
    recent_clients = (Client.query
                      .order_by(Client.created_at.desc())
                      .limit(5).all())

    # ── Low stock items ───────────────────────────────────────
    low_stock = (InventoryItem.query
                 .filter(InventoryItem.available_qty <= 2,
                         InventoryItem.is_active == True)
                 .order_by(InventoryItem.available_qty)
                 .limit(5).all())

    return render_template("dashboard/index.html",
        total_events=total_events,
        active_events=active_events,
        total_clients=total_clients,
        new_inquiries=new_inquiries,
        upcoming=upcoming,
        overdue_tasks=overdue_tasks,
        overdue_payments=overdue_payments,
        recent_clients=recent_clients,
        low_stock=low_stock,
        today=today,
    )
