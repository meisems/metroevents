"""
Metro Events — Event Model
The core "workspace" entity. One Event = One Workspace.

Types: wedding, corporate, birthday, debut, others
Status: planning → production → ready → event_day → done → cancelled
"""

from datetime import datetime
from database import db


EVENT_TYPES = ["wedding", "corporate", "birthday", "debut", "other"]

EVENT_STATUSES = [
    "planning",
    "production",
    "ready",
    "event_day",
    "done",
    "cancelled",
]

STATUS_COLORS = {
    "planning":    "primary",
    "production":  "warning",
    "ready":       "info",
    "event_day":   "success",
    "done":        "secondary",
    "cancelled":   "danger",
}


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)

    # ── Core Info ─────────────────────────────────────────────
    name = db.Column(db.String(200), nullable=False)  # e.g. "JD & Ana Wedding"
    event_type = db.Column(db.String(50), nullable=False, default="wedding")
    status = db.Column(db.String(50), nullable=False, default="planning")

    # ── Client & Venue ────────────────────────────────────────
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"),
                          nullable=False)
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)

    # ── Dates & Times ─────────────────────────────────────────
    event_date = db.Column(db.Date, nullable=False)
    event_time_start = db.Column(db.Time)
    event_time_end = db.Column(db.Time)
    call_time = db.Column(db.Time)          # crew call time
    setup_deadline = db.Column(db.Time)     # latest setup complete

    # ── Coordinator & Team ────────────────────────────────────
    coordinator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    team_notes = db.Column(db.Text)

    # ── Package & Budget ──────────────────────────────────────
    package_name = db.Column(db.String(150))  # e.g. "Metro Gold Package"
    total_budget = db.Column(db.Numeric(12, 2), default=0)

    # ── Color Palette ─────────────────────────────────────────
    color_palette = db.Column(db.String(200))  # comma-sep hex codes

    # ── Meta ──────────────────────────────────────────────────
    internal_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    client = db.relationship("Client", back_populates="events")
    coordinator = db.relationship("User", foreign_keys=[coordinator_id])
    quotes = db.relationship("Quote", back_populates="event",
                             lazy="dynamic", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="event",
                               lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", back_populates="event",
                            lazy="dynamic", cascade="all, delete-orphan")
    checklist_items = db.relationship("ChecklistItem", back_populates="event",
                                      lazy="dynamic", cascade="all, delete-orphan")
    moodboard_pegs = db.relationship("MoodboardPeg", back_populates="event",
                                     lazy="dynamic", cascade="all, delete-orphan")
    reservations = db.relationship("Reservation", back_populates="event",
                                   lazy="dynamic", cascade="all, delete-orphan")
    event_logs = db.relationship("EventLog", back_populates="event",
                                 lazy="dynamic", cascade="all, delete-orphan")

    # ── Helpers ───────────────────────────────────────────────
    @property
    def status_color(self) -> str:
        return STATUS_COLORS.get(self.status, "secondary")

    @property
    def days_until(self) -> int:
        delta = self.event_date - datetime.utcnow().date()
        return delta.days

    @property
    def active_quote(self):
        """Return the latest non-cancelled quote."""
        return (
            self.quotes.filter_by(is_active=True)
            .order_by(db.desc("version"))
            .first()
        )

    @property
    def total_paid(self):
        from models.payment import Payment as P
        result = (
            db.session.query(db.func.sum(P.amount))
            .filter(P.event_id == self.id, P.status == "paid")
            .scalar()
        )
        return result or 0

    @property
    def balance_due(self):
        quote = self.active_quote
        if not quote:
            return 0
        return float(quote.grand_total) - float(self.total_paid)

    def __repr__(self):
        return f"<Event '{self.name}' [{self.event_date}]>"
