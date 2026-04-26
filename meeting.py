"""
Metro Events — Meeting Schedule Model
Tracks client consultations: when, where, and what package was discussed.
"""

from datetime import datetime
from database import db


class Meeting(db.Model):
    __tablename__ = "meetings"

    id           = db.Column(db.Integer, primary_key=True)

    # ── Who ──────────────────────────────────────────────────
    client_name  = db.Column(db.String(120), nullable=False)
    contact_no   = db.Column(db.String(30),  nullable=True)

    # ── When ─────────────────────────────────────────────────
    meeting_date = db.Column(db.Date,        nullable=False)
    meeting_time = db.Column(db.Time,        nullable=False)

    # ── Where ────────────────────────────────────────────────
    location     = db.Column(db.String(200), nullable=False)

    # ── What package ─────────────────────────────────────────
    package_availed = db.Column(db.String(120), nullable=False)
    package_notes   = db.Column(db.Text,        nullable=True)

    # ── Status ───────────────────────────────────────────────
    # "scheduled" | "completed" | "cancelled" | "no_show"
    status       = db.Column(db.String(20), nullable=False, default="scheduled")

    # ── Optional link to an existing Event ───────────────────
    event_id     = db.Column(db.Integer, db.ForeignKey("events.id",
                             ondelete="SET NULL"), nullable=True)
    event        = db.relationship("Event", backref="meetings", lazy="select")

    # ── Timestamps ───────────────────────────────────────────
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    # ── Helpers ──────────────────────────────────────────────
    STATUS_LABELS = {
        "scheduled":  ("Scheduled",  "badge-info"),
        "completed":  ("Completed",  "badge-success"),
        "cancelled":  ("Cancelled",  "badge-danger"),
        "no_show":    ("No Show",    "badge-warning"),
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, ("Unknown", "badge-secondary"))

    @property
    def meeting_datetime(self):
        return datetime.combine(self.meeting_date, self.meeting_time)

    def __repr__(self):
        return f"<Meeting #{self.id} — {self.client_name} on {self.meeting_date}>"
