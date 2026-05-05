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
from datetime import datetime, date, timedelta

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    # 🚨 THE BOUNCER: Kick clients back to the public landing page
    # We check the role immediately to prevent unauthorized access.
    if current_user.role == 'client':
        flash("Please use the Client Portal to manage your events.", "info")
        return redirect(url_for('main.index')) # Ensure this points to your public home route

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
