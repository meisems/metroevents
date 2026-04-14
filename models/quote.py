"""
Metro Events — Quote & QuoteItem Models
Tracks versioned proposals (v1, v2, v3...) with line items, discounts,
add-ons, and PDF generation support.
"""

from datetime import datetime
from database import db


class Quote(db.Model):
    __tablename__ = "quotes"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # ── Version Control ───────────────────────────────────────
    version = db.Column(db.Integer, nullable=False, default=1)
    label = db.Column(db.String(50))           # e.g. "v1 - Initial", "v2 - Revised"
    is_active = db.Column(db.Boolean, default=True)   # only one active at a time
    is_approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(150))    # client name / signature

    # ── Package ───────────────────────────────────────────────
    package_name = db.Column(db.String(150))
    package_description = db.Column(db.Text)

    # ── Pricing ───────────────────────────────────────────────
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    discount_type = db.Column(db.String(20), default="none")  # none/percent/fixed
    discount_value = db.Column(db.Numeric(10, 2), default=0)
    discount_reason = db.Column(db.String(200))
    tax_percent = db.Column(db.Numeric(5, 2), default=0)
    grand_total = db.Column(db.Numeric(12, 2), default=0)

    # ── Payment Schedule ──────────────────────────────────────
    downpayment_amount = db.Column(db.Numeric(12, 2), default=0)
    downpayment_due = db.Column(db.Date)
    balance_due_date = db.Column(db.Date)

    # ── Notes ─────────────────────────────────────────────────
    inclusions_note = db.Column(db.Text)   # what's included (for PDF)
    exclusions_note = db.Column(db.Text)   # what's NOT included
    terms_note = db.Column(db.Text)        # payment terms

    # ── Meta ──────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", back_populates="quotes")
    items = db.relationship("QuoteItem", back_populates="quote",
                            lazy="dynamic", cascade="all, delete-orphan",
                            order_by="QuoteItem.sort_order")

    # ── Computed helpers ──────────────────────────────────────
    def recalculate(self):
        """Recalculate subtotal, discount, tax, and grand total."""
        sub = sum(float(i.total_price) for i in self.items)
        self.subtotal = sub

        if self.discount_type == "percent":
            disc = sub * float(self.discount_value) / 100
        elif self.discount_type == "fixed":
            disc = float(self.discount_value)
        else:
            disc = 0

        after_disc = sub - disc
        tax = after_disc * float(self.tax_percent) / 100
        self.grand_total = after_disc + tax

    def approve(self, by_name: str):
        self.is_approved = True
        self.approved_at = datetime.utcnow()
        self.approved_by = by_name

    def __repr__(self):
        return f"<Quote event={self.event_id} v{self.version} ₱{self.grand_total}>"


class QuoteItem(db.Model):
    __tablename__ = "quote_items"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=False)

    # ── Item Details ──────────────────────────────────────────
    category = db.Column(db.String(100))       # e.g. "Floral", "Lights", "Backdrop"
    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_addon = db.Column(db.Boolean, default=False)

    # ── Pricing ───────────────────────────────────────────────
    quantity = db.Column(db.Numeric(8, 2), default=1)
    unit = db.Column(db.String(50), default="pc")  # pc, set, lot, hr
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_price = db.Column(db.Numeric(12, 2), default=0)

    # ── Order ─────────────────────────────────────────────────
    sort_order = db.Column(db.Integer, default=0)

    # ── Relationship ──────────────────────────────────────────
    quote = db.relationship("Quote", back_populates="items")

    def save_total(self):
        self.total_price = float(self.quantity) * float(self.unit_price)

    def __repr__(self):
        return f"<QuoteItem '{self.item_name}' x{self.quantity} = ₱{self.total_price}>"
