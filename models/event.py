"""
Metro Events — Event Model
The core "workspace" entity. One Event = One Workspace.
"""

from datetime import datetime
import string
import secrets  # Safer than random for unique IDs
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
    "ready":        "info",
    "event_day":   "success",
    "done":         "secondary",
    "cancelled":   "danger",
}

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    
    # ── NEW: Unique Event ID ──────────────────────────────────
    # format e.g., EVT-X4Y7Z9
    event_id = db.Column(db.String(12), unique=True, nullable=False)

    # ── Core Info ─────────────────────────────────────────────
    name = db.Column(db.String(200), nullable=False)  
    event_type = db.Column(db.String(50), nullable=False, default="wedding")
    status = db.Column(db.String(50), nullable=False, default="planning")

    # ... (rest of your existing columns: client_id, venue, dates, etc.) ...
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time_start = db.Column(db.Time)
    event_time_end = db.Column(db.Time)
    call_time = db.Column(db.Time)
    setup_deadline = db.Column(db.Time)
    coordinator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    team_notes = db.Column(db.Text)
    package_name = db.Column(db.String(150))
    total_budget = db.Column(db.Numeric(12, 2), default=0)
    color_palette = db.Column(db.String(200))
    internal_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    client = db.relationship("Client", back_populates="events")
    coordinator = db.relationship("User", foreign_keys=[coordinator_id])
    quotes = db.relationship("Quote", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    checklist_items = db.relationship("ChecklistItem", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    moodboard_pegs = db.relationship("MoodboardPeg", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    reservations = db.relationship("Reservation", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    event_logs = db.relationship("EventLog", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")

    # ── Static Helper for ID Generation ───────────────────────
    @staticmethod
    def generate_unique_id():
        """Generates a random 6-character uppercase ID like EVT-7B2X9L"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(chars) for _ in range(6))
            new_id = f"EVT-{code}"
            # Check for collisions in the database
            if not Event.query.filter_by(event_id=new_id).first():
                return new_id

    # ── Helpers ───────────────────────────────────────────────
    @property
    def status_color(self) -> str:
        return STATUS_COLORS.get(self.status, "secondary")

    @property
    def days_until(self) -> int:
        delta = self.event_date - datetime.utcnow().date()
        return delta.days

    # ... (rest of your properties: active_quote, total_paid, balance_due) ...

    def __repr__(self):
        return f"<Event '{self.event_id}' - '{self.name}'>"
