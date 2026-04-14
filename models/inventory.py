"""
Metro Events — Inventory & Reservation Models

InventoryItem  → master catalog (what Metro owns/rents out)
Reservation    → ties an item to an event date with qty + condition notes
"""

from datetime import datetime
from database import db


ITEM_CONDITIONS = ["excellent", "good", "fair", "damaged", "missing"]
ITEM_CATEGORIES = [
    "backdrop",
    "draping",
    "lights",
    "flowers",
    "furniture",
    "tableware",
    "linen",
    "signage",
    "props",
    "equipment",
    "other",
]


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)

    # ── Item Info ─────────────────────────────────────────────
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True)             # internal code
    category = db.Column(db.String(50), default="other")
    description = db.Column(db.Text)
    dimensions = db.Column(db.String(150))                  # e.g. "2m x 3m"
    photo_url = db.Column(db.String(300))

    # ── Stock ─────────────────────────────────────────────────
    total_qty = db.Column(db.Integer, nullable=False, default=1)
    available_qty = db.Column(db.Integer, default=1)        # updated on reserve/return
    storage_location = db.Column(db.String(150))            # e.g. "Warehouse A, Shelf 3"

    # ── Financials ────────────────────────────────────────────
    replacement_cost = db.Column(db.Numeric(10, 2))
    rental_price = db.Column(db.Numeric(10, 2))             # if rented externally

    # ── Status ────────────────────────────────────────────────
    is_active = db.Column(db.Boolean, default=True)
    condition = db.Column(db.String(30), default="good")

    # ── Meta ──────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    reservations = db.relationship("Reservation", back_populates="item",
                                   lazy="dynamic")

    def qty_reserved_on(self, event_date) -> int:
        """Return qty already reserved on a specific date."""
        from sqlalchemy import and_
        result = (
            db.session.query(db.func.sum(Reservation.quantity))
            .filter(
                and_(
                    Reservation.item_id == self.id,
                    Reservation.event_date == event_date,
                    Reservation.status != "cancelled",
                )
            )
            .scalar()
        )
        return result or 0

    def qty_available_on(self, event_date) -> int:
        return max(0, self.total_qty - self.qty_reserved_on(event_date))

    def __repr__(self):
        return f"<InventoryItem '{self.name}' qty={self.total_qty}>"


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("inventory_items.id"),
                        nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # ── Reservation Details ───────────────────────────────────
    event_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(
        db.String(30), default="reserved"
    )  # reserved / checked_out / returned / cancelled

    # ── Condition Tracking ────────────────────────────────────
    condition_out = db.Column(db.String(30))     # condition when dispatched
    condition_in = db.Column(db.String(30))      # condition when returned
    condition_notes = db.Column(db.Text)         # e.g. "1 piece chipped"

    # ── Timestamps ────────────────────────────────────────────
    checked_out_at = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    item = db.relationship("InventoryItem", back_populates="reservations")
    event = db.relationship("Event", back_populates="reservations")

    def checkout(self, condition: str = "good"):
        self.status = "checked_out"
        self.condition_out = condition
        self.checked_out_at = datetime.utcnow()

    def return_item(self, condition: str, notes: str = None):
        self.status = "returned"
        self.condition_in = condition
        self.condition_notes = notes
        self.returned_at = datetime.utcnow()

    def __repr__(self):
        return (f"<Reservation item={self.item_id} event={self.event_id} "
                f"qty={self.quantity} [{self.status}]>")
