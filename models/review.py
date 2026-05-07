from database import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    comment = db.Column(db.Text, nullable=False)
    is_featured = db.Column(db.Boolean, default=False) # Admin can check this to show on home page
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    client = db.relationship('Client', backref='reviews')
