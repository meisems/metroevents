"""
Metro Events — After Event Model
Captures post-event feedback, star rating, balance confirmation,
and next booking prompt data.
"""

from datetime import datetime
from database import db


class AfterEvent(db.Model):
    __tablename__ = "after_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"),
                         nullable=False, unique=True)

    # ── Feedback ──────────────────────────────────────────────
    client_feedback = db.Column(db.Text)           # free-text testimonial
    rating_overall = db.Column(db.Integer)         # 1–5 stars
    rating_design = db.Column(db.Integer)
    rating_coordination = db.Column(db.Integer)
    rating_on_time = db.Column(db.Integer)
    rating_crew = db.Column(db.Integer)
    rating_value = db.Column(db.Integer)
    would_recommend = db.Column(db.Boolean)
    allow_testimonial = db.Column(db.Boolean, default=False)

    # ── Wrap-up ───────────────────────────────────────────────
    photos_uploaded = db.Column(db.Boolean, default=False)
    final_balance_settled = db.Column(db.Boolean, default=False)
    balance_settled_date = db.Column(db.Date)

    # ── Next Booking ──────────────────────────────────────────
    next_booking_interest = db.Column(db.Boolean)
    next_event_type = db.Column(db.String(50))
    next_event_notes = db.Column(db.Text)

    # ── Internal Notes ────────────────────────────────────────
    coordinator_notes = db.Column(db.Text)
    issues_encountered = db.Column(db.Text)
    suggestions = db.Column(db.Text)

    # ── Meta ──────────────────────────────────────────────────
    submitted_by_client = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # ── Relationship ──────────────────────────────────────────
    event = db.relationship("Event", backref=db.backref("after_event",
                            uselist=False, cascade="all, delete-orphan"))

    @property
    def avg_rating(self) -> float:
        ratings = [r for r in [
            self.rating_overall, self.rating_design,
            self.rating_coordination, self.rating_on_time,
            self.rating_crew, self.rating_value,
        ] if r is not None]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0.0

    @property
    def star_display(self) -> str:
        r = self.rating_overall or 0
        return "★" * r + "☆" * (5 - r)

    def __repr__(self):
        return f"<AfterEvent event={self.event_id} rating={self.rating_overall}★>"
