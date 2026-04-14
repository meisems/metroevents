"""
Metro Events — User Model
Handles authentication + role-based access control.

Roles:
  admin       → JD / full access, approvals, pricing
  coordinator → timeline, tasks, notes, checklists
  designer    → moodboard, layouts, materials
  warehouse   → inventory, truck loading, in/out scanning
  client      → view proposal, approve designs, payment status
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from database import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.Enum("admin", "coordinator", "designer", "warehouse", "client",
                name="user_roles"),
        nullable=False,
        default="coordinator"
    )
    phone = db.Column(db.String(30))
    avatar_url = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # ── Relationships ─────────────────────────────────────────
    tasks = db.relationship("Task", back_populates="assigned_user",
                            foreign_keys="Task.assigned_to", lazy="dynamic")

    # ── Password helpers ──────────────────────────────────────
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ── Role helpers ──────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_coordinator(self) -> bool:
        return self.role in ("admin", "coordinator")

    @property
    def is_designer(self) -> bool:
        return self.role in ("admin", "designer")

    @property
    def is_warehouse(self) -> bool:
        return self.role in ("admin", "warehouse")

    @property
    def is_client_portal(self) -> bool:
        return self.role == "client"

    def can(self, action: str) -> bool:
        """
        Simple permission matrix.
        action examples: 'approve_quote', 'edit_inventory', 'view_pricing'
        """
        permissions = {
            "admin": ["*"],
            "coordinator": ["view_event", "edit_timeline", "manage_tasks",
                            "edit_checklist", "view_quote"],
            "designer": ["view_event", "edit_moodboard", "view_inventory",
                         "view_checklist"],
            "warehouse": ["view_event", "edit_inventory", "view_checklist",
                          "manage_reservations"],
            "client": ["view_proposal", "approve_design", "view_payment",
                       "upload_pegs"],
        }
        allowed = permissions.get(self.role, [])
        return "*" in allowed or action in allowed

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
