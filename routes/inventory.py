"""
Metro Events — Inventory Routes
Item catalog + reservations per event.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db
from models.inventory import InventoryItem, Reservation, ITEM_CATEGORIES, ITEM_CONDITIONS
from models.event import Event
from datetime import datetime
import os, uuid
from flask import current_app
from werkzeug.utils import secure_filename

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")

ALLOWED = {"png","jpg","jpeg","gif"}

def save_photo(file):
    if file and "." in file.filename:
        ext = file.filename.rsplit(".",1)[1].lower()
        if ext in ALLOWED:
            fname = f"{uuid.uuid4().hex}.{ext}"
            folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, fname))
            return f"/static/uploads/{fname}"
    return None


@inventory_bp.route("/")
@login_required
def list_items():
    cat_filter = request.args.get("cat", "")
    search     = request.args.get("q", "").strip()
    page       = request.args.get("page", 1, type=int)
    q = InventoryItem.query.filter_by(is_active=True)
    if cat_filter:
        q = q.filter_by(category=cat_filter)
    if search:
        q = q.filter(InventoryItem.name.ilike(f"%{search}%"))
    items = q.order_by(InventoryItem.category, InventoryItem.name).paginate(page=page, per_page=24)
    return render_template("inventory/list.html",
        items=items, categories=ITEM_CATEGORIES,
        cat_filter=cat_filter, search=search,
    )


@inventory_bp.route("/new", methods=["GET","POST"])
@login_required
def new_item():
    if not (current_user.is_admin or current_user.is_warehouse):
        flash("Access denied.", "danger")
        return redirect(url_for("inventory.list_items"))
    if request.method == "POST":
        photo_url = save_photo(request.files.get("photo"))
        item = InventoryItem(
            name             = request.form.get("name","").strip(),
            sku              = request.form.get("sku","").strip() or None,
            category         = request.form.get("category","other"),
            description      = request.form.get("description","").strip(),
            dimensions       = request.form.get("dimensions","").strip(),
            total_qty        = int(request.form.get("total_qty") or 1),
            available_qty    = int(request.form.get("total_qty") or 1),
            storage_location = request.form.get("storage_location","").strip(),
            replacement_cost = float(request.form.get("replacement_cost") or 0) or None,
            rental_price     = float(request.form.get("rental_price") or 0) or None,
            condition        = request.form.get("condition","good"),
            photo_url        = photo_url,
        )
        db.session.add(item)
        db.session.commit()
        flash(f"'{item.name}' added to inventory.", "success")
        return redirect(url_for("inventory.detail", item_id=item.id))
    return render_template("inventory/form.html", item=None,
                           categories=ITEM_CATEGORIES, conditions=ITEM_CONDITIONS)


@inventory_bp.route("/<int:item_id>")
@login_required
def detail(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    reservations = (item.reservations
                    .order_by(Reservation.event_date.desc())
                    .limit(20).all())
    return render_template("inventory/detail.html", item=item,
                           reservations=reservations, conditions=ITEM_CONDITIONS)


@inventory_bp.route("/<int:item_id>/edit", methods=["GET","POST"])
@login_required
def edit_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if not (current_user.is_admin or current_user.is_warehouse):
        flash("Access denied.", "danger")
        return redirect(url_for("inventory.detail", item_id=item_id))
    if request.method == "POST":
        photo_url = save_photo(request.files.get("photo"))
        item.name             = request.form.get("name","").strip()
        item.sku              = request.form.get("sku","").strip() or None
        item.category         = request.form.get("category","other")
        item.description      = request.form.get("description","").strip()
        item.dimensions       = request.form.get("dimensions","").strip()
        item.total_qty        = int(request.form.get("total_qty") or 1)
        item.storage_location = request.form.get("storage_location","").strip()
        item.replacement_cost = float(request.form.get("replacement_cost") or 0) or None
        item.rental_price     = float(request.form.get("rental_price") or 0) or None
        item.condition        = request.form.get("condition","good")
        if photo_url:
            item.photo_url = photo_url
        db.session.commit()
        flash("Item updated.", "success")
        return redirect(url_for("inventory.detail", item_id=item.id))
    return render_template("inventory/form.html", item=item,
                           categories=ITEM_CATEGORIES, conditions=ITEM_CONDITIONS)


@inventory_bp.route("/<int:item_id>/reserve", methods=["POST"])
@login_required
def reserve(item_id):
    item  = InventoryItem.query.get_or_404(item_id)
    event_id   = int(request.form.get("event_id"))
    qty        = int(request.form.get("quantity") or 1)
    raw_date   = request.form.get("event_date","")
    try:
        evt_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date.", "danger")
        return redirect(url_for("inventory.detail", item_id=item_id))
    avail = item.qty_available_on(evt_date)
    if qty > avail:
        flash(f"Only {avail} available on that date.", "warning")
        return redirect(url_for("inventory.detail", item_id=item_id))
    r = Reservation(item_id=item_id, event_id=event_id,
                    event_date=evt_date, quantity=qty)
    db.session.add(r)
    db.session.commit()
    flash(f"Reserved {qty}x '{item.name}' for event.", "success")
    return redirect(url_for("inventory.detail", item_id=item_id))


@inventory_bp.route("/reservations/<int:res_id>/checkout", methods=["POST"])
@login_required
def checkout(res_id):
    r = Reservation.query.get_or_404(res_id)
    r.checkout(condition=request.form.get("condition","good"))
    db.session.commit()
    flash("Item checked out.", "success")
    return redirect(url_for("inventory.detail", item_id=r.item_id))


@inventory_bp.route("/reservations/<int:res_id>/return", methods=["POST"])
@login_required
def return_item(res_id):
    r = Reservation.query.get_or_404(res_id)
    r.return_item(
        condition=request.form.get("condition","good"),
        notes=request.form.get("notes",""),
    )
    db.session.commit()
    flash("Item returned & condition noted.", "success")
    return redirect(url_for("inventory.detail", item_id=r.item_id))
