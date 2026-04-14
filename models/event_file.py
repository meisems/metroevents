"""
Metro Events — EventFile Model
Stores file attachments per event: layouts, permits, contracts,
floor plans, PDFs, reference docs.
"""

from datetime import datetime
from database import db


FILE_CATEGORIES = [
    "floor_plan",
    "layout",
    "permit",
    "contract",
    "reference",
    "invoice",
    "photo",
    "other",
]


class EventFile(db.Model):
    __tablename__ = "event_files"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # ── File Info ─────────────────────────────────────────────
    category = db.Column(db.String(50), default="other")
    original_filename = db.Column(db.String(250), nullable=False)
    stored_filename = db.Column(db.String(300), nullable=False)  # uuid.ext
    file_url = db.Column(db.String(400), nullable=False)
    file_size_kb = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    description = db.Column(db.Text)

    # ── Meta ──────────────────────────────────────────────────
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_client_visible = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    event = db.relationship("Event", backref=db.backref("files",
                            lazy="dynamic", cascade="all, delete-orphan"))
    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    @property
    def extension(self) -> str:
        parts = self.original_filename.rsplit(".", 1)
        return parts[1].lower() if len(parts) == 2 else ""

    @property
    def icon(self) -> str:
        ext_icons = {
            "pdf": "📄", "doc": "📝", "docx": "📝",
            "xls": "📊", "xlsx": "📊",
            "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️",
            "zip": "🗜️", "rar": "🗜️",
        }
        return ext_icons.get(self.extension, "📁")

    def __repr__(self):
        return f"<EventFile '{self.original_filename}' [{self.category}]>"
