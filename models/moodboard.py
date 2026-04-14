"""
Metro Events — Moodboard & Pegs Model
Stores inspiration images, palette references, and design approvals.
"""

from datetime import datetime
from database import db


PEG_CATEGORIES = [
    "overall_theme",
    "flowers",
    "backdrop",
    "table_setting",
    "lighting",
    "color_palette",
    "venue_layout",
    "bride_look",
    "client_uploaded",
    "approved_final",
]


class MoodboardPeg(db.Model):
    __tablename__ = "moodboard_pegs"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # ── Peg Info ──────────────────────────────────────────────
    title = db.Column(db.String(200))
    category = db.Column(db.String(50), default="overall_theme")
    image_url = db.Column(db.String(300), nullable=False)
    source_url = db.Column(db.String(500))     # Pinterest/IG link if online
    notes = db.Column(db.Text)

    # ── Approval ──────────────────────────────────────────────
    is_approved = db.Column(db.Boolean, default=False)
    is_client_uploaded = db.Column(db.Boolean, default=False)  # uploaded via portal
    approved_at = db.Column(db.DateTime)

    # ── Meta ──────────────────────────────────────────────────
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", back_populates="moodboard_pegs")
    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    def approve(self):
        self.is_approved = True
        self.approved_at = datetime.utcnow()

    def __repr__(self):
        approved = "✓" if self.is_approved else "○"
        return f"<MoodboardPeg {approved} '{self.title}' [{self.category}]>"
