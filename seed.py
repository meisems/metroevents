"""
Metro Events — Seed Script
Run once: python seed.py
Creates default admin user + sample data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import db
from models.user import User
from models.client import Client
from models.event import Event
from models.inventory import InventoryItem
from models.supplier import Supplier
from datetime import date, timedelta

app = create_app("development")

with app.app_context():
    db.create_all()

    # ── Admin user ────────────────────────────────────────────
    if not User.query.filter_by(email="admin@metroevents.ph").first():
        admin = User(name="Admin", email="admin@metroevents.ph", role="admin")
        admin.set_password("admin1234")
        db.session.add(admin)
        print("✅ Admin created: admin@metroevents.ph / admin1234")

    # ── Sample coordinator ────────────────────────────────────
    if not User.query.filter_by(email="coordinator@metroevents.ph").first():
        coord = User(name="Maria Coordinator", email="coordinator@metroevents.ph", role="coordinator")
        coord.set_password("metro2024")
        db.session.add(coord)
        print("✅ Coordinator created")

    # ── Sample designer ───────────────────────────────────────
    if not User.query.filter_by(email="designer@metroevents.ph").first():
        des = User(name="Ana Designer", email="designer@metroevents.ph", role="designer")
        des.set_password("metro2024")
        db.session.add(des)
        print("✅ Designer created")

    db.session.flush()

    # ── Sample clients ────────────────────────────────────────
    if Client.query.count() == 0:
        clients_data = [
            ("Maria Santos", "maria@example.com", "+63 912 345 6789", "new_inquiry"),
            ("Jose Reyes",   "jose@example.com",  "+63 917 123 4567", "proposal_sent"),
            ("Ana Dela Cruz","ana@example.com",   "+63 998 765 4321", "fully_booked"),
        ]
        for name, email, phone, stage in clients_data:
            c = Client(full_name=name, email=email, phone=phone, pipeline_stage=stage)
            db.session.add(c)
        print("✅ Sample clients created")
        db.session.flush()

    # ── Sample event ──────────────────────────────────────────
    if Event.query.count() == 0:
        client = Client.query.filter_by(pipeline_stage="fully_booked").first()
        admin_user = User.query.filter_by(role="admin").first()
        if client and admin_user:
            e = Event(
                name         = "Ana & Jose Wedding",
                event_type   = "wedding",
                status       = "production",
                client_id    = client.id,
                coordinator_id = admin_user.id,
                venue_name   = "The Grand Ballroom",
                venue_address= "123 Makati Ave, Makati City",
                event_date   = date.today() + timedelta(days=45),
                package_name = "Metro Gold Package",
                color_palette= "#C9A84C, #FFFFFF, #1A1A2E",
                total_budget = 150000,
            )
            db.session.add(e)
            print("✅ Sample event created")

    # ── Inventory items ───────────────────────────────────────
    if InventoryItem.query.count() == 0:
        inventory_data = [
            ("White Backdrop Frame 3x6m",  "backdrop",   5, "BKD-001"),
            ("Gold Chiavari Chair",         "furniture",  80, "CHR-001"),
            ("Round Table 60-inch",         "furniture",  20, "TBL-001"),
            ("Crystal Centerpiece",         "props",      30, "CPC-001"),
            ("LED Uplights (set)",          "lights",     10, "LGT-001"),
            ("Ivory Satin Linen",           "linen",      40, "LIN-001"),
            ("Photo Frame Signage",         "signage",    10, "SGN-001"),
        ]
        for name, cat, qty, sku in inventory_data:
            item = InventoryItem(name=name, category=cat, total_qty=qty,
                                 available_qty=qty, sku=sku)
            db.session.add(item)
        print("✅ Sample inventory created")

    # ── Suppliers ─────────────────────────────────────────────
    if Supplier.query.count() == 0:
        suppliers_data = [
            ("Bloom Florals PH",    "florist",       "Mia Santos", "0917-111-2222"),
            ("SoundPro Systems",    "Sound System",  "Carlo Reyes","0922-333-4444"),
            ("QuickPrint Studio",   "Printing",      "Beth Lim",   "0933-555-6666"),
        ]
        for company, cat, contact, phone in suppliers_data:
            s = Supplier(company_name=company, category=cat,
                         contact_person=contact, phone=phone)
            db.session.add(s)
        print("✅ Sample suppliers created")

    db.session.commit()
    print("\n🎉 Seed complete! Run: python run.py")
    print("   Login: admin@metroevents.ph / metro2024")
