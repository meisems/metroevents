"""
Metro Events — Quotes Routes
Versioned proposals with line items, discounts, PDF export.
"""
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, make_response)
from flask_login import login_required, current_user
from database import db
from models.quote import Quote, QuoteItem
from models.event import Event
from datetime import datetime

quotes_bp = Blueprint("quotes", __name__, url_prefix="/events")


def _latest_version(event_id):
    q = Quote.query.filter_by(event_id=event_id).order_by(Quote.version.desc()).first()
    return q.version if q else 0


@quotes_bp.route("/<int:event_id>/quotes/new", methods=["GET", "POST"])
@login_required
def new_quote(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        # deactivate previous quotes
        Quote.query.filter_by(event_id=event_id, is_active=True).update({"is_active": False})
        version = _latest_version(event_id) + 1
        q = Quote(
            event_id            = event_id,
            version             = version,
            label               = request.form.get("label") or f"v{version}",
            package_name        = request.form.get("package_name", "").strip(),
            package_description = request.form.get("package_description", "").strip(),
            discount_type       = request.form.get("discount_type", "none"),
            discount_value      = float(request.form.get("discount_value") or 0),
            discount_reason     = request.form.get("discount_reason", "").strip(),
            tax_percent         = float(request.form.get("tax_percent") or 0),
            inclusions_note     = request.form.get("inclusions_note", "").strip(),
            exclusions_note     = request.form.get("exclusions_note", "").strip(),
            terms_note          = request.form.get("terms_note", "").strip(),
            downpayment_amount  = float(request.form.get("downpayment_amount") or 0),
            is_active           = True,
        )
        raw_dp  = request.form.get("downpayment_due")
        raw_bal = request.form.get("balance_due_date")
        if raw_dp:
            try: q.downpayment_due = datetime.strptime(raw_dp, "%Y-%m-%d").date()
            except ValueError: pass
        if raw_bal:
            try: q.balance_due_date = datetime.strptime(raw_bal, "%Y-%m-%d").date()
            except ValueError: pass
        db.session.add(q)
        db.session.flush()  # get id

        # line items (submitted as arrays)
        names       = request.form.getlist("item_name[]")
        categories  = request.form.getlist("item_category[]")
        descs       = request.form.getlist("item_desc[]")
        qtys        = request.form.getlist("item_qty[]")
        units       = request.form.getlist("item_unit[]")
        prices      = request.form.getlist("item_price[]")
        addons      = request.form.getlist("item_addon[]")

        for i, name in enumerate(names):
            if not name.strip():
                continue
            qty   = float(qtys[i] if i < len(qtys) else 1)
            price = float(prices[i] if i < len(prices) else 0)
            item  = QuoteItem(
                quote_id   = q.id,
                item_name  = name.strip(),
                category   = categories[i] if i < len(categories) else "",
                description= descs[i] if i < len(descs) else "",
                quantity   = qty,
                unit       = units[i] if i < len(units) else "pc",
                unit_price = price,
                is_addon   = str(i) in addons,
                sort_order = i,
            )
            item.save_total()
            db.session.add(item)

        db.session.flush()
        q.recalculate()
        db.session.commit()
        flash(f"Quote v{version} created!", "success")
        return redirect(url_for("events.detail", event_id=event_id, tab="quote"))
    return render_template("quotes/form.html", event=event, quote=None)


@quotes_bp.route("/<int:event_id>/quotes/<int:quote_id>/approve", methods=["POST"])
@login_required
def approve_quote(event_id, quote_id):
    quote = Quote.query.get_or_404(quote_id)
    by_name = request.form.get("approved_by", current_user.name)
    quote.approve(by_name)
    db.session.commit()
    flash("Quote approved ✅", "success")
    return redirect(url_for("events.detail", event_id=event_id, tab="quote"))


@quotes_bp.route("/<int:event_id>/quotes/<int:quote_id>/pdf")
@login_required
def quote_pdf(event_id, quote_id):
    """Generate a simple PDF proposal using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        import io

        event = Event.query.get_or_404(event_id)
        quote = Quote.query.get_or_404(quote_id)
        items = quote.items.all()

        buf    = io.BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4,
                                   leftMargin=2*cm, rightMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        gold   = colors.HexColor("#C9A84C")
        dark   = colors.HexColor("#1A1A2E")

        h1 = ParagraphStyle("H1", parent=styles["Title"],
                             textColor=dark, fontSize=22, spaceAfter=4)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                             textColor=gold, fontSize=13, spaceBefore=14)
        body = styles["Normal"]
        right_style = ParagraphStyle("Right", parent=body, alignment=TA_RIGHT)

        story = []

        # ── Header ─────────────────────────────────────────────
        story.append(Paragraph("METRO EVENTS", h1))
        story.append(Paragraph("<i>Creating memories.</i>",
                                ParagraphStyle("tag", parent=body,
                                               textColor=gold, fontSize=11)))
        story.append(HRFlowable(width="100%", thickness=2, color=gold,
                                spaceAfter=8))
        story.append(Paragraph(f"PROPOSAL — {quote.label or f'v{quote.version}'}",
                                ParagraphStyle("label", parent=body,
                                               fontSize=10, textColor=colors.grey)))
        story.append(Spacer(1, 0.3*cm))

        # ── Event Info ─────────────────────────────────────────
        story.append(Paragraph("Event Details", h2))
        info_data = [
            ["Event:", event.name],
            ["Client:", event.client.full_name],
            ["Date:", event.event_date.strftime("%B %d, %Y") if event.event_date else "—"],
            ["Venue:", event.venue_name or "—"],
            ["Package:", quote.package_name or "—"],
        ]
        info_tbl = Table(info_data, colWidths=[4*cm, 12*cm])
        info_tbl.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
            ("FONTNAME",  (0,0), (0,-1),  "Helvetica-Bold"),
            ("FONTSIZE",  (0,0), (-1,-1), 10),
            ("TEXTCOLOR", (0,0), (0,-1),  dark),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(info_tbl)
        story.append(Spacer(1, 0.4*cm))

        # ── Line Items ─────────────────────────────────────────
        story.append(Paragraph("Inclusions", h2))
        header_row = [
            Paragraph("<b>Category</b>", body),
            Paragraph("<b>Item</b>", body),
            Paragraph("<b>Qty</b>", body),
            Paragraph("<b>Unit</b>", body),
            Paragraph("<b>Unit Price</b>", body),
            Paragraph("<b>Total</b>", body),
        ]
        rows = [header_row]
        for it in items:
            rows.append([
                it.category or "",
                it.item_name,
                str(it.quantity),
                it.unit,
                f"₱{float(it.unit_price):,.2f}",
                f"₱{float(it.total_price):,.2f}",
            ])

        col_w = [3*cm, 6.5*cm, 1.5*cm, 1.5*cm, 3*cm, 3*cm]
        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0),  dark),
            ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
            ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F6EF")]),
            ("ALIGN",        (2,1), (-1,-1), "RIGHT"),
            ("BOTTOMPADDING",(0,0), (-1,-1), 5),
            ("TOPPADDING",   (0,0), (-1,-1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.4*cm))

        # ── Totals ─────────────────────────────────────────────
        totals = [
            ["Subtotal:", f"₱{float(quote.subtotal):,.2f}"],
        ]
        if quote.discount_type != "none":
            disc_label = (f"Discount ({quote.discount_value}%)"
                          if quote.discount_type == "percent"
                          else "Discount (fixed)")
            totals.append([disc_label, f"- ₱{float(quote.discount_value):,.2f}"])
        if float(quote.tax_percent) > 0:
            totals.append([f"Tax ({quote.tax_percent}%):", ""])
        totals.append(["GRAND TOTAL:", f"₱{float(quote.grand_total):,.2f}"])

        tot_tbl = Table(totals, colWidths=[12*cm, 4.5*cm])
        tot_tbl.setStyle(TableStyle([
            ("ALIGN",     (1,0), (1,-1), "RIGHT"),
            ("FONTNAME",  (0,-1),(-1,-1),"Helvetica-Bold"),
            ("FONTSIZE",  (0,0), (-1,-1), 10),
            ("TEXTCOLOR", (0,-1),(-1,-1), gold),
            ("FONTSIZE",  (0,-1),(-1,-1), 13),
            ("LINEABOVE", (0,-1),(-1,-1), 1.5, dark),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ]))
        story.append(tot_tbl)

        # ── Terms ──────────────────────────────────────────────
        if quote.terms_note:
            story.append(Paragraph("Terms & Conditions", h2))
            story.append(Paragraph(quote.terms_note, body))

        # ── Footer ─────────────────────────────────────────────
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=gold))
        story.append(Paragraph(
            "<i>Thank you for choosing Metro Events — Creating memories.</i>",
            ParagraphStyle("footer", parent=body, fontSize=9,
                           textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(story)
        buf.seek(0)
        resp = make_response(buf.read())
        resp.headers["Content-Type"] = "application/pdf"
        safe_name = event.name.replace(" ", "_")
        resp.headers["Content-Disposition"] = (
            f"attachment; filename=Metro_Proposal_{safe_name}_v{quote.version}.pdf"
        )
        return resp

    except ImportError:
        flash("ReportLab not installed. Run: pip install reportlab", "danger")
        return redirect(url_for("events.detail", event_id=event_id, tab="quote"))
