from flask import Blueprint, render_template, redirect, url_for, flash, request
from database import db
from models.client import Client
from models.event import Event
from datetime import datetime  # 👈 This was the missing piece!

public_bp = Blueprint("public", __name__)

@public_bp.route("/inquiry", methods=["POST"])
def submit_inquiry():
    # 1. Get info from the landing page form
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    msg = request.form.get("message", "").strip()
    pkg = request.form.get("package", "Custom")

    # 🟢 THE DUPLICATE BLOCKER 🟢
    client = Client.query.filter_by(email=email).first()

    if not client:
        # If they are new, create the client profile
        client = Client(
            full_name=name,
            email=email,
            phone=phone,
            notes=f"PACKAGE REQUEST: {pkg}\nMESSAGE: {msg}"
        )
        db.session.add(client)
        db.session.flush() 
    else:
        # 🟢 Now this line will work perfectly!
        client.notes = (client.notes or "") + f"\n\n--- NEW REQUEST ({datetime.now().date()}) ---\nPKG: {pkg}\nMSG: {msg}"
        flash(f"Welcome back {name}! We received your new request.", "info")

    # 2. Create the Event Request and attach it to the client
    new_event = Event(
        client_id=client.id,
        name=f"{pkg} Request - {name}",
        status="new_inquiry"
    )
    
    db.session.add(new_event)
    db.session.commit()

    flash("Your inquiry has been sent! We will contact you soon. ✨", "success")
    
    # Make sure 'index' exists in your public_bp, otherwise use "/"
    return redirect("/")b
