"""
Metro Events — Entry Point
Run: python run.py
Then open: http://localhost:5000
"""

import os
from app import create_app
from database import db
from models import *   # noqa — ensures all models are registered

app = create_app(os.environ.get("FLASK_ENV", "development"))


def seed_admin():
    """Create default admin user if none exists."""
    from models.user import User
    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="Admin",
            email="admin@metroevents.ph",
            role="admin",
            phone="+63 9XX XXX XXXX",
            is_active=True,
        )
        admin.set_password("admin1234")
        db.session.add(admin)
        db.session.commit()
        print("✅  Admin user created: admin@metroevents.ph / admin1234")
    else:
        print("ℹ️   Admin user already exists.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_admin()
        print("🎉  Metro Events is running → http://localhost:5000")

    app.run(debug=True, host="0.0.0.0", port=5000)
