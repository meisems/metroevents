"""
Metro Events — Meeting Schedules Routes
Blueprint: meetings_bp  |  URL prefix: /meetings
"""

from datetime import date, datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, jsonify)
from flask_login import login_required
from database import db
from models.meeting import Meeting

meetings_bp = Blueprint("meetings", __name__, url_prefix="/meetings")

# ── Helpers ───────────────────────────────────────────────────────────────

PACKAGES = [
    "Silver Package",
    "Gold Package",
    "Platinum Package",
    "Diamond Package",
    "Custom / TBD",
]

STATUS_OPTIONS = ["scheduled", "completed", "cancelled", "no_show"]


def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _parse_time(s):
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time()
        except (ValueError, TypeError):
            pass
    return None


# ── List / Dashboard ──────────────────────────────────────────────────────

@meetings_bp.route("/")
@login_required
def index():
    status_filter = request.args.get("status", "")
    date_from     = request.args.get("date_from", "")
    date_to       = request.args.get("date_to", "")
    search        = request.args.get("q", "").strip()

    query = Meeting.query

    if status_filter:
        query = query.filter(Meeting.status == status_filter)
    if date_from and _parse_date(date_from):
        query = query.filter(Meeting.meeting_date >= _parse_date(date_from))
    if date_to and _parse_date(date_to):
        query = query.filter(Meeting.meeting_date <= _parse_date(date_to))
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Meeting.client_name.ilike(like),
                Meeting.location.ilike(like),
                Meeting.package_availed.ilike(like),
            )
        )

    meetings = query.order_by(
        Meeting.meeting_date.asc(),
        Meeting.meeting_time.asc()
    ).all()

    # Summary counts for stat cards
    today = date.today()
    stats = {
        "total":     Meeting.query.count(),
        "today":     Meeting.query.filter(Meeting.meeting_date == today).count(),
        "upcoming":  Meeting.query.filter(
                         Meeting.meeting_date > today,
                         Meeting.status == "scheduled"
                     ).count(),
        "completed": Meeting.query.filter(Meeting.status == "completed").count(),
    }

    return render_template(
        "meetings/index.html",
        meetings=meetings,
        stats=stats,
        packages=PACKAGES,
        status_options=STATUS_OPTIONS,
        filters={
            "status": status_filter,
            "date_from": date_from,
            "date_to": date_to,
            "q": search,
        },
        today=today,
    )


# ── Create ────────────────────────────────────────────────────────────────

@meetings_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        mtg = Meeting(
            client_name     = request.form.get("client_name", "").strip(),
            contact_no      = request.form.get("contact_no", "").strip(),
            meeting_date    = _parse_date(request.form.get("meeting_date")),
            meeting_time    = _parse_time(request.form.get("meeting_time")),
            location        = request.form.get("location", "").strip(),
            package_availed = request.form.get("package_availed", "").strip(),
            package_notes   = request.form.get("package_notes", "").strip(),
            status          = request.form.get("status", "scheduled"),
            event_id        = request.form.get("event_id") or None,
        )

        if not mtg.client_name or not mtg.meeting_date or not mtg.meeting_time:
            flash("Client name, date, and time are required.", "danger")
            return redirect(url_for("meetings.new"))

        db.session.add(mtg)
        db.session.commit()
        flash(f"Meeting with {mtg.client_name} scheduled!", "success")
        return redirect(url_for("meetings.index"))

    # Populate event dropdown
    try:
        from models.event import Event
        events = Event.query.order_by(Event.id.desc()).all()
    except Exception:
        events = []

    return render_template(
        "meetings/form.html",
        meeting=None,
        packages=PACKAGES,
        status_options=STATUS_OPTIONS,
        events=events,
    )


# ── Edit ──────────────────────────────────────────────────────────────────

@meetings_bp.route("/<int:meeting_id>/edit", methods=["GET", "POST"])
@login_required
def edit(meeting_id):
    mtg = Meeting.query.get_or_404(meeting_id)

    if request.method == "POST":
        mtg.client_name     = request.form.get("client_name", "").strip()
        mtg.contact_no      = request.form.get("contact_no", "").strip()
        mtg.meeting_date    = _parse_date(request.form.get("meeting_date"))
        mtg.meeting_time    = _parse_time(request.form.get("meeting_time"))
        mtg.location        = request.form.get("location", "").strip()
        mtg.package_availed = request.form.get("package_availed", "").strip()
        mtg.package_notes   = request.form.get("package_notes", "").strip()
        mtg.status          = request.form.get("status", mtg.status)
        mtg.event_id        = request.form.get("event_id") or None

        db.session.commit()
        flash("Meeting updated.", "success")
        return redirect(url_for("meetings.index"))

    try:
        from models.event import Event
        events = Event.query.order_by(Event.id.desc()).all()
    except Exception:
        events = []

    return render_template(
        "meetings/form.html",
        meeting=mtg,
        packages=PACKAGES,
        status_options=STATUS_OPTIONS,
        events=events,
    )


# ── Delete ────────────────────────────────────────────────────────────────

@meetings_bp.route("/<int:meeting_id>/delete", methods=["POST"])
@login_required
def delete(meeting_id):
    mtg = Meeting.query.get_or_404(meeting_id)
    db.session.delete(mtg)
    db.session.commit()
    flash("Meeting deleted.", "info")
    return redirect(url_for("meetings.index"))


# ── Status Toggle (AJAX) ──────────────────────────────────────────────────

@meetings_bp.route("/<int:meeting_id>/status", methods=["POST"])
@login_required
def update_status(meeting_id):
    mtg    = Meeting.query.get_or_404(meeting_id)
    new_st = request.json.get("status")
    if new_st in STATUS_OPTIONS:
        mtg.status = new_st
        db.session.commit()
        return jsonify({"ok": True, "status": mtg.status})
    return jsonify({"ok": False}), 400
