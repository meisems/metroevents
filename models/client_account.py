"""
Metro Events — Client Account Model
Links User accounts (role='client') to Client records for portal access.
"""

from datetime import datetime
from database import db


class ClientAccount(db.Model):
    """
    Bridge table between User (auth) and Client (CRM).
    Allows clients to sign up, login, and self-serve orders.
    """
    __tablename__ = "client_accounts"

    id = db.Column(db.Integer, primary_key=True)
    
    # ── References ─────────────────────────────────────────────
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                       unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), 
                         unique=True, nullable=True, index=True)
    
    # ── Status ─────────────────────────────────────────────────
    # pending → approved (admin review required)
    account_status = db.Column(
        db.String(20), 
        nullable=False, 
        default="pending"  # pending, approved, suspended
    )
    
    # ── Verification ──────────────────────────────────────────
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(128), unique=True)
    verification_sent_at = db.Column(db.DateTime)
    verified_at = db.Column(db.DateTime)
    
    # ── Meta ───────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    # ── Relationships ──────────────────────────────────────────
    user = db.relationship("User", foreign_keys=[user_id], 
                          backref="client_account")
    client = db.relationship("Client", backref="account")
    approved_by = db.relationship("User", foreign_keys=[approved_by_user_id])
    
    def approve(self, approved_by_id: int):
        """Admin approval of client account."""
        self.account_status = "approved"
        self.approved_at = datetime.utcnow()
        self.approved_by_user_id = approved_by_id
    
    def suspend(self):
        """Suspend client account access."""
        self.account_status = "suspended"
    
    def is_approved(self) -> bool:
        return self.account_status == "approved"
    
    def __repr__(self):
        return f"<ClientAccount {self.user.email} [{self.account_status}]>"
