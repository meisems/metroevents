"""
Metro Events — Supplier Hub Routes
Full CRUD for suppliers, purchase orders, and delivery tracking.
"""

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from database import db
from models.supplier import Supplier, PurchaseOrder
from models.event import Event
from datetime import datetime
import os, uuid
from flask import current_app

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")

ALLOWED = {"png", "jpg", "jpeg", "gif", "pdf"}


def save_proof(file):
    if file and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext in ALLOWED:
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, fname))
            return f"/static/uploads/{fname}"
    return None


# ─── SUPPLIER LIST ────────────────────────────────────────────────────────

@suppliers_bp.route("/")
@login_required
def list_suppliers():
    cat_filter    = request.args.get("cat", "")
    search        = request.args.get("q", "").strip()
    preferred_only = request.args.get("preferred") == "1"
    page          = request.args.get("page", 1, type=int)

    q = Supplier.query.filter_by(is_active=True)
    if cat_filter:
        q = q.filter_by(category=cat_filter)
    if preferred_only:
        q = q.filter_by(is_preferred=True)
    if search:
        q = q.filter(Supplier.company_name.ilike(f"%{search}%"))

    suppliers = q.order_by(Supplier.is_preferred.desc(),
                           Supplier.company_name).paginate(page=page, per_page=20)

    # Distinct categories for filter dropdown
    categories = [r[0] for r in db.session.query(Supplier.category).distinct()
                  if r[0]]
    return render_template("suppliers/list.html",
        suppliers=suppliers, categories=categories,
        cat_filter=cat_filter, search=search,
        preferred_only=preferred_only,
    )


# ─── NEW SUPPLIER ─────────────────────────────────────────────────────────

@suppliers_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_supplier():
    if not current_user.is_admin and not current_user.is_coordinator:
        flash("Access denied.", "danger")
        return redirect(url_for("suppliers.list_suppliers"))
    if request.method == "POST":
        s = Supplier(
            company_name   = request.form.get("company_name", "").strip(),
            contact_person = request.form.get("contact_person", "").strip(),
            category       = request.form.get("category", "").strip(),
            email          = request.form.get("email", "").strip(),
            phone          = request.form.get("phone", "").strip(),
            address        = request.form.get("address", "").strip(),
            notes          = request.form.get("notes", "").strip(),
            is_preferred   = request.form.get("is_preferred") == "1",
        )
        db.session.add(s)
        db.session.commit()
        flash(f"Supplier '{s.company_name}' added.", "success")
        return redirect(url_for("suppliers.detail", supplier_id=s.id))
    return render_template("suppliers/form.html", supplier=None)


# ─── DETAIL ───────────────────────────────────────────────────────────────

@suppliers_bp.route("/<int:supplier_id>")
@login_required
def detail(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    pos = (supplier.purchase_orders
           .order_by(PurchaseOrder.created_at.desc()).all())
    events = Event.query.order_by(Event.event_date.desc()).limit(30).all()
    return render_template("suppliers/detail.html",
        supplier=supplier, pos=pos, events=events,
    )


# ─── EDIT ─────────────────────────────────────────────────────────────────

@suppliers_bp.route("/<int:supplier_id>/edit", methods=["GET", "POST"])
@login_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if not current_user.is_admin and not current_user.is_coordinator:
        flash("Access denied.", "danger")
        return redirect(url_for("suppliers.detail", supplier_id=supplier_id))
    if request.method == "POST":
        supplier.company_name   = request.form.get("company_name", "").strip()
        supplier.contact_person = request.form.get("contact_person", "").strip()
        supplier.category       = request.form.get("category", "").strip()
        supplier.email          = request.form.get("email", "").strip()
        supplier.phone          = request.form.get("phone", "").strip()
        supplier.address        = request.form.get("address", "").strip()
        supplier.notes          = request.form.get("notes", "").strip()
        supplier.is_preferred   = request.form.get("is_preferred") == "1"
        rating_raw              = request.form.get("rating")
        if rating_raw:
            try:
                supplier.rating = float(rating_raw)
            except ValueError:
                pass
        db.session.commit()
        flash("Supplier updated.", "success")
        return redirect(url_for("suppliers.detail", supplier_id=supplier.id))
    return render_template("suppliers/form.html", supplier=supplier)


# ─── DEACTIVATE ───────────────────────────────────────────────────────────

@suppliers_bp.route("/<int:supplier_id>/deactivate", methods=["POST"])
@login_required
def deactivate(supplier_id):
    if not current_user.is_admin:
        flash("Only admins can deactivate suppliers.", "danger")
        return redirect(url_for("suppliers.detail", supplier_id=supplier_id))
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    db.session.commit()
    flash(f"'{supplier.company_name}' deactivated.", "warning")
    return redirect(url_for("suppliers.list_suppliers"))


# ─── PURCHASE ORDERS ──────────────────────────────────────────────────────

@suppliers_bp.route("/<int:supplier_id>/po/add", methods=["POST"])
@login_required
def add_po(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    proof_url = save_proof(request.files.get("proof_file"))
    po = PurchaseOrder(
        supplier_id          = supplier.id,
        event_id             = int(request.form.get("event_id")) if request.form.get("event_id") else None,
        po_number            = request.form.get("po_number", "").strip(),
        description          = request.form.get("description", "").strip(),
        amount               = float(request.form.get("amount") or 0),
        status               = request.form.get("status", "pending"),
        delivery_time_window = request.form.get("delivery_time_window", "").strip(),
        downpayment_amount   = float(request.form.get("downpayment_amount") or 0) or None,
        balance_amount       = float(request.form.get("balance_amount") or 0) or None,
        proof_of_payment_url = proof_url,
    )
    for field, fmt in [("delivery_date", "%Y-%m-%d"),
                       ("downpayment_paid_date", "%Y-%m-%d"),
                       ("balance_paid_date", "%Y-%m-%d")]:
        raw = request.form.get(field)
        if raw:
            try:
                setattr(po, field, datetime.strptime(raw, fmt).date())
            except ValueError:
                pass
    db.session.add(po)
    db.session.commit()
    flash(f"PO {po.po_number or '#' + str(po.id)} added.", "success")
    return redirect(url_for("suppliers.detail", supplier_id=supplier_id))


@suppliers_bp.route("/po/<int:po_id>/mark_delivered", methods=["POST"])
@login_required
def mark_delivered(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    on_time = request.form.get("on_time") == "1"
    notes   = request.form.get("notes", "").strip()
    po.mark_delivered(on_time=on_time, notes=notes)
    db.session.commit()
    flash("Delivery recorded ✅" if on_time else "Delivery recorded (late) ⚠️",
          "success" if on_time else "warning")
    return redirect(url_for("suppliers.detail", supplier_id=po.supplier_id))


@suppliers_bp.route("/po/<int:po_id>/upload_proof", methods=["POST"])
@login_required
def upload_proof(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    proof_url = save_proof(request.files.get("proof_file"))
    if proof_url:
        po.proof_of_payment_url = proof_url
        db.session.commit()
        flash("Proof of payment uploaded.", "success")
    else:
        flash("No valid file uploaded.", "warning")
    return redirect(url_for("suppliers.detail", supplier_id=po.supplier_id))
