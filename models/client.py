"""
Metro Events — Client Model
Tracks client info + their inquiry pipeline stage.

CRM Pipeline stages:
  new_inquiry → ocular_scheduled → proposal_sent →
  reserved → fully_booked → done → cancelled
"""

from datetime import datetime
from database import db


PIPELINE_STAGES = [
    "new_inquiry",
    "ocular_scheduled",
    "proposal_sent",
    "reserved",
    "fully_booked",
    "done",
    "cancelled",
]

PIPELINE_LABELS = {
    "new_inquiry":       ("🔔 New Inquiry",        "primary"),
    "ocular_scheduled":  ("📅 Ocular Scheduled",   "info"),
    "proposal_sent":     ("📄 Proposal Sent",       "warning"),
    "reserved":          ("✅ Reserved",             "success"),
    "fully_booked":      ("🎉 Fully Booked",        "success"),
    "done":              ("🏁 Done",                 "secondary"),
    "cancelled":         ("❌ Cancelled",            "danger"),
}

NEXT_ACTION = {
    "new_inquiry":       "Schedule Ocular",
    "ocular_scheduled":  "Send Proposal",
    "proposal_sent":     "Follow Up",
    "reserved":          "Confirm Full Booking",
    "fully_booked":      "Prepare Event",
    "done":              "Request Feedback",
    "cancelled":         None,
}


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)

    # ── Basic Info ────────────────────────────────────────────
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), index=True)
    phone = db.Column(db.String(30))
    instagram = db.Column(db.String(100))
    address = db.Column(db.Text)
    referred_by = db.Column(db.String(150))   # referral source
    notes = db.Column(db.Text)                # internal notes

    # ── CRM Pipeline ─────────────────────────────────────────
    pipeline_stage = db.Column(
        db.String(50), nullable=False, default="new_inquiry"
    )
    inquiry_date = db.Column(db.DateTime, default=datetime.utcnow)
    ocular_date = db.Column(db.DateTime)
    last_contacted = db.Column(db.DateTime)

    # ── Meta ──────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    events = db.relationship("Event", back_populates="client",
                             lazy="dynamic", cascade="all, delete-orphan")

    # ── Helpers ───────────────────────────────────────────────
    @property
    def stage_label(self) -> str:
        return PIPELINE_LABELS.get(self.pipeline_stage, ("Unknown", "secondary"))[0]

    @property
    def stage_color(self) -> str:
        return PIPELINE_LABELS.get(self.pipeline_stage, ("Unknown", "secondary"))[1]

    @property
    def next_action(self) -> str | None:
        return NEXT_ACTION.get(self.pipeline_stage)

    def advance_stage(self):
        """Move client to the next pipeline stage."""
        try:
            idx = PIPELINE_STAGES.index(self.pipeline_stage)
            if idx < len(PIPELINE_STAGES) - 2:  # don't advance past 'done'
                self.pipeline_stage = PIPELINE_STAGES[idx + 1]
        except ValueError:
            pass

    @property
    def total_events(self) -> int:
        return self.events.count()

    def __repr__(self):
        return f"<Client {self.full_name} [{self.pipeline_stage}]>"
