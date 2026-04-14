"""
Metro Events — Payment Model
Tracks payment schedules, status, and proof of payment uploads.
"""

from datetime import datetime
from database import db


PAYMENT_STATUSES = ["pending", "paid", "partial", "overdue", "refunded"]
PAYMENT_TYPES = ["downpayment", "midpayment", "balance", "addon", "refund"]


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"))

    # ── Payment Details ───────────────────────────────────────
    payment_type = db.Column(db.String(50), default="downpayment")
    label = db.Column(db.String(150))          # e.g. "Downpayment", "Balance"
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    status = db.Column(db.String(30), default="pending")

    # ── Payment Method ────────────────────────────────────────
    method = db.Column(db.String(50))         # cash/gcash/bank/check
    reference_number = db.Column(db.String(100))
    proof_of_payment_url = db.Column(db.String(300))  # uploaded screenshot

    # ── Notes ─────────────────────────────────────────────────
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", back_populates="payments")

    # ── Helpers ───────────────────────────────────────────────
    @property
    def is_overdue(self) -> bool:
        if self.status == "pending" and self.due_date:
            return self.due_date < datetime.utcnow().date()
        return False

    @property
    def status_color(self) -> str:
        return {
            "pending":  "warning",
            "paid":     "success",
            "partial":  "info",
            "overdue":  "danger",
            "refunded": "secondary",
        }.get(self.status, "secondary")

    def mark_paid(self, method: str = None, reference: str = None):
        self.status = "paid"
        self.paid_date = datetime.utcnow().date()
        if method:
            self.method = method
        if reference:
            self.reference_number = reference

    def __repr__(self):
        return f"<Payment ₱{self.amount} [{self.status}] event={self.event_id}>"
