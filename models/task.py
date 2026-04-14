"""
Metro Events — Task Model
Covers Crew Assignments + Production Tasks + Event Day timeline ticks.

Categories:
  pre_production  → fabrication, coordination, design approvals
  supplier        → delivery windows, follow-ups
  load_in         → truck loading, site setup
  event_day       → time-based crew tasks during event
  load_out        → pack-down, return items
  post_event      → billing, feedback, archival
"""

from datetime import datetime
from database import db


TASK_CATEGORIES = [
    "pre_production",
    "supplier",
    "load_in",
    "event_day",
    "load_out",
    "post_event",
]

TASK_PRIORITIES = ["low", "normal", "high", "urgent"]


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))

    # ── Task Info ─────────────────────────────────────────────
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default="pre_production")
    priority = db.Column(db.String(20), default="normal")

    # ── Scheduling ────────────────────────────────────────────
    due_date = db.Column(db.Date)
    due_time = db.Column(db.Time)           # for event-day tasks (e.g. 14:00)
    estimated_minutes = db.Column(db.Integer)

    # ── Status ────────────────────────────────────────────────
    is_done = db.Column(db.Boolean, default=False)
    done_at = db.Column(db.DateTime)
    done_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # ── Meta ──────────────────────────────────────────────────
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", back_populates="tasks")
    assigned_user = db.relationship("User", foreign_keys=[assigned_to],
                                    back_populates="tasks")
    done_by = db.relationship("User", foreign_keys=[done_by_id])

    # ── Helpers ───────────────────────────────────────────────
    @property
    def priority_color(self) -> str:
        return {
            "low":    "secondary",
            "normal": "primary",
            "high":   "warning",
            "urgent": "danger",
        }.get(self.priority, "primary")

    @property
    def is_overdue(self) -> bool:
        if not self.is_done and self.due_date:
            return self.due_date < datetime.utcnow().date()
        return False

    def mark_done(self, user_id: int):
        self.is_done = True
        self.done_at = datetime.utcnow()
        self.done_by_id = user_id

    def __repr__(self):
        status = "✓" if self.is_done else "○"
        return f"<Task {status} '{self.title}' [{self.category}]>"
