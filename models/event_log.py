"""
Metro Events — Event Day Log Model
Tracks incidents, change requests, notes, and sign-offs during event day.
"""

from datetime import datetime
from database import db


LOG_TYPES = [
    "note",
    "incident",
    "change_request",
    "client_approval",
    "sign_off",
    "timeline_tick",
]

LOG_TYPE_COLORS = {
    "note":            "secondary",
    "incident":        "danger",
    "change_request":  "warning",
    "client_approval": "success",
    "sign_off":        "success",
    "timeline_tick":   "info",
}


class EventLog(db.Model):
    __tablename__ = "event_logs"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    logged_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    # ── Log Entry ─────────────────────────────────────────────
    log_type = db.Column(db.String(50), nullable=False, default="note")
    message = db.Column(db.Text, nullable=False)
    photo_url = db.Column(db.String(300))       # optional photo evidence

    # ── Change Request specifics ──────────────────────────────
    change_description = db.Column(db.Text)
    cost_impact = db.Column(db.Numeric(10, 2))  # extra cost if change requested
    is_approved_by_client = db.Column(db.Boolean)
    approved_by_name = db.Column(db.String(150))

    # ── Timestamps ────────────────────────────────────────────
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", back_populates="event_logs")
    logger = db.relationship("User", foreign_keys=[logged_by])

    @property
    def type_color(self) -> str:
        return LOG_TYPE_COLORS.get(self.log_type, "secondary")

    @property
    def type_icon(self) -> str:
        return {
            "note":            "📝",
            "incident":        "⚠️",
            "change_request":  "🔄",
            "client_approval": "✅",
            "sign_off":        "🏁",
            "timeline_tick":   "⏰",
        }.get(self.log_type, "📌")

    def __repr__(self):
        return f"<EventLog [{self.log_type}] @ {self.logged_at:%H:%M} '{self.message[:40]}'>"
