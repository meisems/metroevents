"""
Metro Events — Supplier & PurchaseOrder Models
Tracks external vendors: florists, caterers, printers, rental houses, etc.
"""

from datetime import datetime
from database import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)

    # ── Info ──────────────────────────────────────────────────
    company_name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(150))
    category = db.Column(db.String(100))   # e.g. "Florist", "Sound System", "Catering"
    email = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)

    # ── Performance ───────────────────────────────────────────
    rating = db.Column(db.Numeric(3, 1), default=5.0)  # 1.0 - 5.0
    on_time_count = db.Column(db.Integer, default=0)
    late_count = db.Column(db.Integer, default=0)
    issue_count = db.Column(db.Integer, default=0)

    # ── Meta ──────────────────────────────────────────────────
    is_preferred = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    purchase_orders = db.relationship("PurchaseOrder", back_populates="supplier",
                                      lazy="dynamic", cascade="all, delete-orphan")

    @property
    def reliability_pct(self) -> float:
        total = self.on_time_count + self.late_count
        return round(self.on_time_count / total * 100, 1) if total else 100.0

    def __repr__(self):
        return f"<Supplier '{self.company_name}' [{self.category}]>"


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"),
                            nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))

    # ── PO Details ────────────────────────────────────────────
    po_number = db.Column(db.String(50))               # e.g. "PO-2024-001"
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(
        db.String(30), default="pending"
    )  # pending / downpaid / fully_paid / delivered / cancelled

    # ── Delivery ──────────────────────────────────────────────
    delivery_date = db.Column(db.Date)
    delivery_time_window = db.Column(db.String(100))   # e.g. "8:00 AM - 10:00 AM"
    actual_delivery_at = db.Column(db.DateTime)
    was_on_time = db.Column(db.Boolean)
    delivery_notes = db.Column(db.Text)

    # ── Payment ───────────────────────────────────────────────
    downpayment_amount = db.Column(db.Numeric(10, 2))
    downpayment_paid_date = db.Column(db.Date)
    balance_amount = db.Column(db.Numeric(10, 2))
    balance_paid_date = db.Column(db.Date)
    proof_of_payment_url = db.Column(db.String(300))

    # ── Meta ──────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    supplier = db.relationship("Supplier", back_populates="purchase_orders")

    def mark_delivered(self, on_time: bool, notes: str = None):
        self.actual_delivery_at = datetime.utcnow()
        self.was_on_time = on_time
        self.delivery_notes = notes
        self.status = "delivered"
        # update supplier stats
        if on_time:
            self.supplier.on_time_count += 1
        else:
            self.supplier.late_count += 1

    def __repr__(self):
        return f"<PO '{self.po_number}' ₱{self.amount} [{self.status}]>"
