"""
Metro Events — Checklist Model
Pre-production, fabrication, load-in/out checklists per event.
Templates can be preloaded per event type (wedding, corporate, birthday).
"""

from datetime import datetime
from database import db


CHECKLIST_PHASES = [
    "pre_production",
    "fabrication",
    "supplier",
    "load_in",
    "event_day",
    "load_out",
    "post_event",
]


class ChecklistItem(db.Model):
    __tablename__ = "checklist_items"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # ── Item Info ─────────────────────────────────────────────
    phase = db.Column(db.String(50), nullable=False, default="pre_production")
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    responsible_role = db.Column(db.String(50))    # coordinator/designer/warehouse
    due_date = db.Column(db.Date)
    sort_order = db.Column(db.Integer, default=0)

    # ── Status ────────────────────────────────────────────────
    is_done = db.Column(db.Boolean, default=False)
    done_at = db.Column(db.DateTime)
    done_by = db.Column(db.String(100))            # name of who ticked it off
    notes = db.Column(db.Text)

    # ── Meta ──────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", back_populates="checklist_items")

    def tick(self, by_name: str):
        self.is_done = True
        self.done_at = datetime.utcnow()
        self.done_by = by_name

    def untick(self):
        self.is_done = False
        self.done_at = None
        self.done_by = None

    def __repr__(self):
        status = "✓" if self.is_done else "○"
        return f"<ChecklistItem {status} [{self.phase}] '{self.title}'>"


# ── Template definitions ───────────────────────────────────────────────────
CHECKLIST_TEMPLATES = {
    "wedding": [
        # Pre-production
        ("pre_production", "Client ocular / site visit",         "coordinator"),
        ("pre_production", "Finalize floor plan layout",         "designer"),
        ("pre_production", "Get signed quote / contract",        "coordinator"),
        ("pre_production", "Confirm downpayment received",       "coordinator"),
        ("pre_production", "Order flowers from supplier",        "coordinator"),
        ("pre_production", "Confirm backdrop design with client","designer"),
        ("pre_production", "Brief full team on event details",   "coordinator"),
        # Fabrication
        ("fabrication",    "Build backdrop structure",           "warehouse"),
        ("fabrication",    "Prepare centerpiece prototypes",     "designer"),
        ("fabrication",    "Cut & prep draping fabric",         "warehouse"),
        ("fabrication",    "Print signage & table names",        "designer"),
        # Supplier
        ("supplier",       "Confirm flower delivery schedule",   "coordinator"),
        ("supplier",       "Confirm sound system setup time",    "coordinator"),
        ("supplier",       "Get caterer layout requirements",    "coordinator"),
        # Load-in
        ("load_in",        "Load truck — inventory per list",    "warehouse"),
        ("load_in",        "Arrive at venue on schedule",        "warehouse"),
        ("load_in",        "Set up backdrop & draping",          "warehouse"),
        ("load_in",        "Place centerpieces on tables",       "designer"),
        ("load_in",        "Final styling walkthrough",          "designer"),
        ("load_in",        "Client approval of setup",           "coordinator"),
        # Load-out
        ("load_out",       "Count & pack all inventory",         "warehouse"),
        ("load_out",       "Check condition of returned items",  "warehouse"),
        ("load_out",       "Return supplier rentals",            "warehouse"),
        # Post-event
        ("post_event",     "Send final balance invoice",         "coordinator"),
        ("post_event",     "Request client feedback/rating",     "coordinator"),
        ("post_event",     "Upload event photos to file tab",    "designer"),
        ("post_event",     "Update inventory conditions",        "warehouse"),
    ],
    "corporate": [
        ("pre_production", "Get event brief from client",        "coordinator"),
        ("pre_production", "Confirm booth size & layout",        "designer"),
        ("pre_production", "Permits & venue coordination",       "coordinator"),
        ("fabrication",    "Build booth structure",              "warehouse"),
        ("fabrication",    "Prepare branding materials",         "designer"),
        ("load_in",        "Load and deliver booth",             "warehouse"),
        ("load_in",        "Set up AV equipment",               "warehouse"),
        ("load_out",       "Dismantle and pack booth",           "warehouse"),
        ("post_event",     "Send completion report to client",   "coordinator"),
    ],
    "birthday": [
        ("pre_production", "Confirm theme & color palette",      "designer"),
        ("pre_production", "Reserve venue & date",               "coordinator"),
        ("fabrication",    "Create themed backdrop",             "designer"),
        ("fabrication",    "Prep balloon arrangements",          "designer"),
        ("load_in",        "Setup & styling",                    "warehouse"),
        ("load_in",        "Photo wall / selfie booth setup",    "designer"),
        ("load_out",       "Teardown & inventory return",        "warehouse"),
        ("post_event",     "Send final invoice",                 "coordinator"),
    ],
}


def apply_template(event, template_key: str):
    """Apply a checklist template to an event. Returns list of ChecklistItem."""
    items = []
    template = CHECKLIST_TEMPLATES.get(template_key, [])
    for order, (phase, title, role) in enumerate(template):
        item = ChecklistItem(
            event_id=event.id,
            phase=phase,
            title=title,
            responsible_role=role,
            sort_order=order,
        )
        items.append(item)
    return items
