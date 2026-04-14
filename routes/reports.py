"""
Metro Events — Reports & Analytics Routes
Monthly bookings, conversion rate, inventory utilization,
supplier performance, and post-event feedback scores.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import db
from models.event import Event
from models.client import Client, PIPELINE_STAGES
from models.payment import Payment
from models.inventory import InventoryItem, Reservation
from models.supplier import Supplier, PurchaseOrder
from models.after_event import AfterEvent
from models.task import Task
from sqlalchemy import func, extract, and_
from datetime import datetime, date, timedelta

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def require_admin(f):
    from functools import wraps
    from flask import flash, redirect, url_for
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash("Reports are admin-only.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


# ─── DASHBOARD ────────────────────────────────────────────────────────────

@reports_bp.route("/")
@login_required
@require_admin
def index():
    year  = request.args.get("year", datetime.utcnow().year, type=int)
    month = request.args.get("month", 0, type=int)  # 0 = all year

    # Monthly bookings for the year
    monthly = []
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    for m in range(1, 13):
        count = (Event.query
                 .filter(extract("year", Event.event_date) == year,
                         extract("month", Event.event_date) == m)
                 .count())
        revenue = (db.session.query(func.sum(Payment.amount))
                   .join(Event, Event.id == Payment.event_id)
                   .filter(Payment.status == "paid",
                           extract("year", Event.event_date) == year,
                           extract("month", Event.event_date) == m)
                   .scalar()) or 0
        monthly.append({"month": month_names[m-1], "count": count,
                        "revenue": float(revenue)})

    # Conversion rate (pipeline funnel)
    funnel = {}
    for stage in PIPELINE_STAGES:
        funnel[stage] = Client.query.filter_by(pipeline_stage=stage).count()

    total_inquiries = sum(funnel.values())
    booked = funnel.get("fully_booked", 0) + funnel.get("done", 0)
    conversion_rate = round(booked / total_inquiries * 100, 1) if total_inquiries else 0

    # Event type breakdown
    type_counts = (db.session.query(Event.event_type, func.count(Event.id))
                   .filter(extract("year", Event.event_date) == year)
                   .group_by(Event.event_type).all())

    # Top revenue events
    top_events = (db.session.query(Event,
                                   func.sum(Payment.amount).label("total_paid"))
                  .join(Payment, Payment.event_id == Event.id)
                  .filter(Payment.status == "paid",
                          extract("year", Event.event_date) == year)
                  .group_by(Event.id)
                  .order_by(func.sum(Payment.amount).desc())
                  .limit(5).all())

    # Post-event avg ratings
    avg_ratings = (db.session.query(
        func.avg(AfterEvent.rating_overall).label("overall"),
        func.avg(AfterEvent.rating_design).label("design"),
        func.avg(AfterEvent.rating_coordination).label("coord"),
        func.avg(AfterEvent.rating_on_time).label("ontime"),
        func.avg(AfterEvent.rating_crew).label("crew"),
        func.avg(AfterEvent.rating_value).label("value"),
    ).join(Event, Event.id == AfterEvent.event_id)
     .filter(extract("year", Event.event_date) == year)
     .first())

    return render_template("reports/index.html",
        year=year, monthly=monthly, funnel=funnel,
        total_inquiries=total_inquiries, booked=booked,
        conversion_rate=conversion_rate, type_counts=type_counts,
        top_events=top_events, avg_ratings=avg_ratings,
        years=list(range(datetime.utcnow().year - 2,
                         datetime.utcnow().year + 2)),
    )


# ─── INVENTORY UTILIZATION ────────────────────────────────────────────────

@reports_bp.route("/inventory")
@login_required
@require_admin
def inventory_report():
    items = InventoryItem.query.filter_by(is_active=True).all()
    utilization = []
    for item in items:
        total_res = item.reservations.filter(
            Reservation.status != "cancelled"
        ).count()
        utilization.append({
            "item": item,
            "total_reservations": total_res,
        })
    utilization.sort(key=lambda x: x["total_reservations"], reverse=True)
    return render_template("reports/inventory.html", utilization=utilization)


# ─── SUPPLIER PERFORMANCE ─────────────────────────────────────────────────

@reports_bp.route("/suppliers")
@login_required
@require_admin
def supplier_report():
    suppliers = (Supplier.query.filter_by(is_active=True)
                 .order_by(Supplier.reliability_pct.desc()).all())
    return render_template("reports/suppliers.html", suppliers=suppliers)


# ─── FEEDBACK SCORES ──────────────────────────────────────────────────────

@reports_bp.route("/feedback")
@login_required
@require_admin
def feedback_report():
    year = request.args.get("year", datetime.utcnow().year, type=int)
    entries = (AfterEvent.query
               .join(Event, Event.id == AfterEvent.event_id)
               .filter(extract("year", Event.event_date) == year)
               .order_by(Event.event_date.desc()).all())
    return render_template("reports/feedback.html",
        entries=entries, year=year,
        years=list(range(datetime.utcnow().year - 2,
                         datetime.utcnow().year + 2)),
    )


# ─── API: chart data (JSON) ───────────────────────────────────────────────

@reports_bp.route("/api/monthly_revenue")
@login_required
def api_monthly_revenue():
    year = request.args.get("year", datetime.utcnow().year, type=int)
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    data = []
    for m in range(1, 13):
        rev = (db.session.query(func.sum(Payment.amount))
               .join(Event, Event.id == Payment.event_id)
               .filter(Payment.status == "paid",
                       extract("year", Event.event_date) == year,
                       extract("month", Event.event_date) == m)
               .scalar()) or 0
        data.append({"month": month_names[m-1], "revenue": float(rev)})
    return jsonify(data)
