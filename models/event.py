"""
Metro Events — Event Model
The core "workspace" entity. One Event = One Workspace.
"""
import string
import secrets
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

    # ── Unique ID ─────────────────────────────────────────────
    # Format: EVT-X4Y7Z2 (Generated via generate_unique_id)
    event_id = db.Column(db.String(12), unique=True, nullable=False)

    # ── Core Info ─────────────────────────────────────────────
    name = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default="wedding")
    status = db.Column(db.String(50), nullable=False, default="planning")

    # ── Client & Venue ────────────────────────────────────────
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)

    # ── Dates & Times ─────────────────────────────────────────
    event_date = db.Column(db.Date, nullable=False)
    event_time_start = db.Column(db.Time)
    event_time_end = db.Column(db.Time)
    call_time = db.Column(db.Time)
    setup_deadline = db.Column(db.Time)

    # ── Coordinator & Team ────────────────────────────────────
    coordinator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    team_notes = db.Column(db.Text)

    # ── Package & Budget ──────────────────────────────────────
    package_name = db.Column(db.String(150))
    total_budget = db.Column(db.Numeric(12, 2), default=0)
    color_palette = db.Column(db.String(200)) # comma-sep hex codes

    # ── Meta ──────────────────────────────────────────────────
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
    purchase_orders = db.relationship("PurchaseOrder", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")

    # ── Static Methods ────────────────────────────────────────
    @staticmethod
    def generate_unique_id():
        """Generates a random 6-character ID like EVT-A1B2C3"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(chars) for _ in range(6))
            new_id = f"EVT-{code}"
            # Ensure it doesn't exist in the database already
            if not Event.query.filter_by(event_id=new_id).first():
                return new_id

    # ── Financial Properties ──────────────────────────────────
    @property
    def total_paid(self):
        """Sum of all confirmed payments."""
        from models.payment import Payment # Local import to avoid circular dependency
        import sqlalchemy as sa
        result = db.session.query(sa.func.sum(Payment.amount)).filter(
            Payment.event_id == self.id, 
            Payment.status == "paid"
        ).scalar()
        return float(result or 0)

    @property
    def balance_due(self):
        """Grand total minus payments. Returns 0.0 if no quote exists."""
        quote = self.active_quote
        if not quote:
            return 0.0
        total = float(quote.grand_total or 0)
        paid = float(self.total_paid)
        return round(total - paid, 2)

    @property
    def downpayment_status(self):
        """Calculates 50% downpayment progress."""
        quote = self.active_quote
        if not quote:
            return 0.0
        total = float(quote.grand_total or 0)
        required = total * 0.5
        paid = float(self.total_paid)
        if paid >= required:
            return "Cleared"
        return round(required - paid, 2)

    # ── View Helpers ──────────────────────────────────────────
    @property
    def active_quote(self):
        """Returns the latest active quote version."""
        import sqlalchemy as sa
        return self.quotes.filter_by(is_active=True).order_by(sa.desc('version')).first()

    @property
    def status_color(self) -> str:
        return STATUS_COLORS.get(self.status, "secondary")

    @property
    def days_until(self) -> int:
        delta = self.event_date - datetime.utcnow().date()
        return delta.days

    def __repr__(self):
        return f"<Event '{self.event_id}' - '{self.name}'>"
