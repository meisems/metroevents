"""
Metro Events — Smart Reminders & Auto-Reply Templates
Provides:
  - Reminder alerts API (balance due, downpayment, supplier)
  - Taglish auto-reply template generation
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import db
from models.event import Event
from models.payment import Payment
from models.supplier import PurchaseOrder
from models.client import Client
from datetime import datetime, date, timedelta

reminders_bp = Blueprint("reminders", __name__, url_prefix="/reminders")


# ─── REMINDERS DASHBOARD ──────────────────────────────────────────────────

@reminders_bp.route("/")
@login_required
def index():
    today = date.today()
    in_7  = today + timedelta(days=7)
    in_3  = today + timedelta(days=3)

    # Upcoming events (next 7 days)
    upcoming_events = (Event.query
        .filter(Event.event_date >= today,
                Event.event_date <= in_7,
                Event.status.in_(["planning","production","ready"]))
        .order_by(Event.event_date).all())

    # Overdue payments
    overdue_payments = (Payment.query
        .filter(Payment.status == "pending",
                Payment.due_date < today)
        .order_by(Payment.due_date).limit(20).all())

    # Payments due in 3 days
    due_soon_payments = (Payment.query
        .filter(Payment.status == "pending",
                Payment.due_date >= today,
                Payment.due_date <= in_3)
        .order_by(Payment.due_date).limit(20).all())

    # Supplier deliveries due today/tomorrow
    supplier_due = (PurchaseOrder.query
        .filter(PurchaseOrder.delivery_date >= today,
                PurchaseOrder.delivery_date <= today + timedelta(days=2),
                PurchaseOrder.status.in_(["pending","downpaid"]))
        .order_by(PurchaseOrder.delivery_date).all())

    # Clients with no contact in 7+ days (in proposal_sent stage)
    stale_date = datetime.utcnow() - timedelta(days=7)
    stale_clients = (Client.query
        .filter(Client.pipeline_stage == "proposal_sent",
                (Client.last_contacted == None) |
                (Client.last_contacted < stale_date))
        .order_by(Client.last_contacted).limit(10).all())

    return render_template("reminders/index.html",
        today=today,
        upcoming_events=upcoming_events,
        overdue_payments=overdue_payments,
        due_soon_payments=due_soon_payments,
        supplier_due=supplier_due,
        stale_clients=stale_clients,
    )


# ─── TAGLISH TEMPLATES ────────────────────────────────────────────────────

TEMPLATES = {
    "inquiry_auto_reply": {
        "label": "New Inquiry Auto-Reply",
        "subject": "Salamat sa inyong inquiry — Metro Events",
        "body": (
            "Hi {client_name}! 🎉\n\n"
            "Salamat sa pag-inquire sa Metro Events — Creating Memories!\n\n"
            "Natanggap na namin ang inyong mensahe tungkol sa "
            "{event_type} sa {event_date}. "
            "Excited kaming makatulong sa paglikha ng unforgettable experience para sa inyo!\n\n"
            "Makikipag-ugnayan sa inyo ang aming team within 24 hours "
            "para ma-discuss ang inyong vision at ma-schedule ang ocular visit.\n\n"
            "Kung may urgent na katanungan, pwede kayong mag-message directly sa:\n"
            "📱 {contact_number}\n\n"
            "Hanggang sa muli,\n"
            "Metro Events Team\n"
            "✨ Creating memories."
        )
    },
    "ocular_confirmation": {
        "label": "Ocular Schedule Confirmation",
        "subject": "Confirmed: Ocular Visit — Metro Events",
        "body": (
            "Hi {client_name}! 😊\n\n"
            "Confirmed na ang inyong ocular visit!\n\n"
            "📅 Date: {ocular_date}\n"
            "🕐 Time: {ocular_time}\n"
            "📍 Venue: {venue_name}\n\n"
            "Dito namin tatalikurin ang bawat detalye ng inyong {event_type} "
            "para masiguro na perpekto ang lahat.\n\n"
            "Kung may ibang tanong o kailangan ng reschedule, "
            "huwag mag-atubiling mag-message!\n\n"
            "See you soon! ✨\n"
            "Metro Events Team"
        )
    },
    "proposal_sent": {
        "label": "Proposal Sent Follow-up",
        "subject": "Metro Events Proposal — {event_name}",
        "body": (
            "Hi {client_name}! 🌟\n\n"
            "Napadala na namin ang inyong proposal para sa {event_name}. "
            "Paki-review ang attached na PDF at huwag mag-atubiling "
            "magtanong kung may gustong baguhin o i-customize.\n\n"
            "💰 Package Total: ₱{total_amount}\n"
            "📅 Event Date: {event_date}\n"
            "📍 Venue: {venue_name}\n\n"
            "Kapag na-approve na, kailangan lang ng downpayment na "
            "₱{downpayment} para ma-secure ang inyong date. 🔒\n\n"
            "Excited na kaming maging bahagi ng inyong espesyal na araw!\n\n"
            "Metro Events Team\n"
            "✨ Creating memories."
        )
    },
    "follow_up": {
        "label": "Follow-up (No Response)",
        "subject": "Kamusta? — Metro Events",
        "body": (
            "Hi {client_name}! 👋\n\n"
            "Kamusta kayo? Just checking in — napadala na namin "
            "ang inyong proposal kamakailan at gusto naming malaman "
            "kung may katanungan kayo o gusto ninyong i-adjust ang kahit ano.\n\n"
            "Available kami para sa Zoom call o personal na meeting "
            "kung gusto ninyong ma-discuss ang mga detalye. "
            "Nandito lang kami para sa inyo! 😊\n\n"
            "Huwag mag-atubiling mag-reply sa message na ito o tawagan kami sa:\n"
            "📱 {contact_number}\n\n"
            "Salamat at sana makapag-usap tayo soon!\n\n"
            "Metro Events Team\n"
            "✨ Creating memories."
        )
    },
    "balance_reminder": {
        "label": "Balance Due Reminder",
        "subject": "Reminder: Balance Due — {event_name}",
        "body": (
            "Hi {client_name}! 🔔\n\n"
            "Friendly reminder lang — malapit na ang due date ng balance "
            "para sa {event_name}.\n\n"
            "💰 Balance Amount: ₱{balance_amount}\n"
            "📅 Due Date: {due_date}\n\n"
            "Maaaring mag-bayad sa pamamagitan ng:\n"
            "• GCash: {gcash_number}\n"
            "• Bank Transfer: {bank_details}\n"
            "• Cash (sa opisina namin)\n\n"
            "Pagkatapos mag-bayad, please send ang proof of payment. "
            "Maraming salamat! 🙏\n\n"
            "Metro Events Team\n"
            "✨ Creating memories."
        )
    },
    "booking_confirmed": {
        "label": "Fully Booked Confirmation",
        "subject": "Confirmed! Fully Booked — {event_name} 🎉",
        "body": (
            "Hi {client_name}! 🎊\n\n"
            "FULLY BOOKED NA! 🥳\n\n"
            "Masaya kaming i-confirm na ang {event_name} ay officially "
            "nakapasok na sa aming calendar!\n\n"
            "📅 Event Date: {event_date}\n"
            "📍 Venue: {venue_name}\n"
            "🎨 Package: {package_name}\n\n"
            "Ang aming team ay magsisimula nang mag-plan at mag-prepare "
            "para sa inyong espesyal na araw. Mabibigyan kayo ng update "
            "sa bawat yugto ng preparation.\n\n"
            "Excited na kaming maging bahagi ng inyong memories! ✨\n\n"
            "Metro Events Team\n"
            "✨ Creating memories."
        )
    },
    "post_event_feedback": {
        "label": "Post-Event Feedback Request",
        "subject": "Kumusta ang {event_name}? — Metro Events",
        "body": (
            "Hi {client_name}! 💛\n\n"
            "Hope you're still floating on cloud nine pagkatapos ng "
            "inyong {event_type}! 🎉\n\n"
            "Gusto naming malaman ang inyong karanasan kasama kami. "
            "Makakatulong ito sa amin na mas mapahusay pa ang aming serbisyo.\n\n"
            "Paki-click ang link para ibahagi ang inyong feedback:\n"
            "🔗 {feedback_link}\n\n"
            "Isang malaking SALAMAT sa inyong tiwala sa Metro Events! "
            "Sana muli kaming makapagsilbi sa inyong susunod na espesyal na okasyon. 🙏\n\n"
            "Metro Events Team\n"
            "✨ Creating memories."
        )
    },
}


@reminders_bp.route("/templates")
@login_required
def templates():
    client_id = request.args.get("client_id", type=int)
    event_id  = request.args.get("event_id", type=int)
    tpl_key   = request.args.get("template", "inquiry_auto_reply")

    client = Client.query.get(client_id) if client_id else None
    event  = Event.query.get(event_id) if event_id else None

    # Build substitution context
    ctx = {
        "client_name":    client.full_name if client else "[Client Name]",
        "event_type":     event.event_type.title() if event else "[Event Type]",
        "event_name":     event.name if event else "[Event Name]",
        "event_date":     event.event_date.strftime("%B %d, %Y") if event and event.event_date else "[Event Date]",
        "venue_name":     event.venue_name if event else "[Venue]",
        "package_name":   event.package_name if event else "[Package]",
        "total_amount":   f"{float(event.active_quote.grand_total):,.2f}" if event and event.active_quote else "0.00",
        "downpayment":    f"{float(event.active_quote.downpayment_amount):,.2f}" if event and event.active_quote else "0.00",
        "balance_amount": f"{float(event.balance_due):,.2f}" if event else "0.00",
        "due_date":       "[Due Date]",
        "ocular_date":    client.ocular_date.strftime("%B %d, %Y") if client and client.ocular_date else "[Ocular Date]",
        "ocular_time":    "[Time]",
        "contact_number": "[Contact Number]",
        "gcash_number":   "[GCash Number]",
        "bank_details":   "[Bank Name / Account Number]",
        "feedback_link":  f"[Feedback URL for event {event_id}]" if event_id else "[Feedback URL]",
    }

    tpl = TEMPLATES.get(tpl_key)
    rendered_subject = tpl["subject"].format_map(ctx) if tpl else ""
    rendered_body    = tpl["body"].format_map(ctx) if tpl else ""

    clients = Client.query.order_by(Client.full_name).all()
    events  = Event.query.order_by(Event.event_date.desc()).limit(50).all()

    return render_template("reminders/templates.html",
        templates=TEMPLATES, tpl_key=tpl_key,
        rendered_subject=rendered_subject, rendered_body=rendered_body,
        clients=clients, events=events,
        selected_client=client, selected_event=event,
    )


@reminders_bp.route("/api/template")
@login_required
def api_template():
    """JSON endpoint for template preview (AJAX)."""
    tpl_key   = request.args.get("template", "inquiry_auto_reply")
    client_id = request.args.get("client_id", type=int)
    event_id  = request.args.get("event_id", type=int)

    client = Client.query.get(client_id) if client_id else None
    event  = Event.query.get(event_id) if event_id else None

    ctx = {
        "client_name":  client.full_name if client else "[Client Name]",
        "event_type":   event.event_type.title() if event else "[Event Type]",
        "event_name":   event.name if event else "[Event Name]",
        "event_date":   event.event_date.strftime("%B %d, %Y") if event and event.event_date else "[Date]",
        "venue_name":   event.venue_name if event else "[Venue]",
        "package_name": event.package_name if event else "[Package]",
        "total_amount": f"{float(event.active_quote.grand_total):,.2f}" if event and event.active_quote else "0.00",
        "downpayment":  f"{float(event.active_quote.downpayment_amount):,.2f}" if event and event.active_quote else "0.00",
        "balance_amount": f"{float(event.balance_due):,.2f}" if event else "0.00",
        "due_date":     "[Due Date]",
        "ocular_date":  client.ocular_date.strftime("%B %d, %Y") if client and client.ocular_date else "[Ocular Date]",
        "ocular_time":  "[Time]",
        "contact_number": "[Contact Number]",
        "gcash_number": "[GCash Number]",
        "bank_details": "[Bank Name / Account Number]",
        "feedback_link": f"/portal/event/{event_id}/feedback" if event_id else "[Feedback URL]",
    }

    tpl = TEMPLATES.get(tpl_key, {})
    return jsonify({
        "subject": tpl.get("subject", "").format_map(ctx),
        "body":    tpl.get("body", "").format_map(ctx),
    })
