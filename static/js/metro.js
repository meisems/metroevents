/* ============================================================
   METRO EVENTS — Main JavaScript
   ============================================================ */

"use strict";

/* ── Mobile sidebar toggle ──────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  const sidebar   = document.querySelector(".me-sidebar");
  const toggleBtn = document.getElementById("sidebarToggle");
  const overlay   = document.getElementById("sidebarOverlay");

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      if (overlay) overlay.classList.toggle("show");
    });
  }
  if (overlay) {
    overlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      overlay.classList.remove("show");
    });
  }

  /* ── Auto-dismiss flash alerts ─────────────────────────── */
  document.querySelectorAll(".me-alert[data-auto-dismiss]").forEach(el => {
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateY(-8px)";
      el.style.transition = "all .4s ease";
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  /* ── Checklist AJAX tick ────────────────────────────────── */
  document.querySelectorAll(".check-box[data-tick-url]").forEach(box => {
    box.addEventListener("click", async () => {
      const url  = box.dataset.tickUrl;
      const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrf || "",
          },
        });
        const data = await res.json();
        const item = box.closest(".checklist-item");
        if (data.done) {
          box.classList.add("checked");
          box.innerHTML = "✓";
          item?.classList.add("done");
        } else {
          box.classList.remove("checked");
          box.innerHTML = "";
          item?.classList.remove("done");
        }
        updateChecklistProgress(item?.closest("[data-checklist]"));
      } catch (e) {
        console.error("Checklist tick failed", e);
      }
    });
  });

  /* ── Task AJAX done toggle ─────────────────────────────── */
  document.querySelectorAll(".task-toggle[data-url]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const url  = btn.dataset.url;
      const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
      try {
        await fetch(url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrf || "",
          },
        });
        const row = btn.closest("tr");
        row?.classList.toggle("task-done-row");
        btn.dataset.url = btn.dataset.altUrl;
        btn.dataset.altUrl = url;
        btn.classList.toggle("btn-success");
        btn.classList.toggle("btn-outline-secondary");
        const icon = btn.querySelector(".task-icon");
        if (icon) icon.textContent = icon.textContent === "✓" ? "○" : "✓";
      } catch (e) { console.error("Task toggle failed", e); }
    });
  });

  /* ── Quote builder — dynamic line items ─────────────────── */
  initQuoteBuilder();

  /* ── Confirm delete dialogs ─────────────────────────────── */
  document.querySelectorAll("form[data-confirm]").forEach(form => {
    form.addEventListener("submit", e => {
      const msg = form.dataset.confirm || "Are you sure?";
      if (!confirm(msg)) e.preventDefault();
    });
  });

  /* ── Color palette preview ──────────────────────────────── */
  const paletteInput = document.getElementById("colorPaletteInput");
  const palettePreview = document.getElementById("colorPalettePreview");
  if (paletteInput && palettePreview) {
    paletteInput.addEventListener("input", () => {
      renderSwatches(paletteInput.value, palettePreview);
    });
    renderSwatches(paletteInput.value, palettePreview);
  }

  /* ── Image preview on upload ────────────────────────────── */
  document.querySelectorAll("input[type=file][data-preview]").forEach(inp => {
    inp.addEventListener("change", () => {
      const previewId = inp.dataset.preview;
      const preview   = document.getElementById(previewId);
      if (preview && inp.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
          preview.src = e.target.result;
          preview.style.display = "block";
        };
        reader.readAsDataURL(inp.files[0]);
      }
    });
  });
});

/* ── Quote builder helpers ──────────────────────────────────── */
function initQuoteBuilder() {
  const tbody = document.getElementById("quoteItemsBody");
  const addBtn = document.getElementById("addQuoteItem");
  if (!tbody || !addBtn) return;

  addBtn.addEventListener("click", () => {
    const idx = tbody.querySelectorAll("tr").length;
    const row = buildItemRow(idx);
    tbody.insertAdjacentHTML("beforeend", row);
    attachRowListeners(tbody.lastElementChild);
    recalcQuote();
  });

  tbody.querySelectorAll("tr").forEach(r => attachRowListeners(r));
  recalcQuote();
}

function buildItemRow(idx) {
  return `
  <tr>
    <td><input class="me-form-control" name="item_category[]" placeholder="Category" /></td>
    <td><input class="me-form-control" name="item_name[]" placeholder="Item name" required /></td>
    <td><input class="me-form-control item-qty" name="item_qty[]" type="number" value="1" min="0.01" step="0.01" style="width:70px" /></td>
    <td>
      <select class="me-form-control" name="item_unit[]" style="width:70px">
        <option>pc</option><option>set</option><option>lot</option><option>hr</option><option>day</option>
      </select>
    </td>
    <td><input class="me-form-control item-price" name="item_price[]" type="number" value="0" min="0" step="0.01" style="width:110px" /></td>
    <td class="item-total text-end" style="font-weight:700">₱0.00</td>
    <td><input type="checkbox" name="item_addon[]" value="${idx}" title="Is add-on?" /></td>
    <td>
      <button type="button" class="btn btn-sm btn-outline-danger remove-row" title="Remove">✕</button>
    </td>
  </tr>`;
}

function attachRowListeners(row) {
  row.querySelectorAll(".item-qty, .item-price").forEach(inp => {
    inp.addEventListener("input", () => { updateRowTotal(row); recalcQuote(); });
  });
  const removeBtn = row.querySelector(".remove-row");
  if (removeBtn) removeBtn.addEventListener("click", () => { row.remove(); recalcQuote(); });
}

function updateRowTotal(row) {
  const qty   = parseFloat(row.querySelector(".item-qty")?.value || 0);
  const price = parseFloat(row.querySelector(".item-price")?.value || 0);
  const total = qty * price;
  const cell  = row.querySelector(".item-total");
  if (cell) cell.textContent = "₱" + total.toLocaleString("en-PH", {minimumFractionDigits: 2});
  return total;
}

function recalcQuote() {
  const tbody = document.getElementById("quoteItemsBody");
  if (!tbody) return;

  let subtotal = 0;
  tbody.querySelectorAll("tr").forEach(row => { subtotal += updateRowTotal(row); });

  const discType  = document.getElementById("discountType")?.value || "none";
  const discVal   = parseFloat(document.getElementById("discountValue")?.value || 0);
  const taxPct    = parseFloat(document.getElementById("taxPercent")?.value || 0);

  let disc = 0;
  if (discType === "percent") disc = subtotal * discVal / 100;
  else if (discType === "fixed") disc = discVal;

  const afterDisc = subtotal - disc;
  const tax       = afterDisc * taxPct / 100;
  const grand     = afterDisc + tax;

  setText("calcSubtotal", fmt(subtotal));
  setText("calcDiscount", fmt(disc));
  setText("calcTax",      fmt(tax));
  setText("calcGrandTotal", fmt(grand));
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = "₱" + val;
}

function fmt(n) {
  return n.toLocaleString("en-PH", {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

/* ── Checklist progress bar ─────────────────────────────────── */
function updateChecklistProgress(container) {
  if (!container) return;
  const total  = container.querySelectorAll(".checklist-item").length;
  const done   = container.querySelectorAll(".checklist-item.done").length;
  const pct    = total ? Math.round(done / total * 100) : 0;
  const bar    = container.querySelector(".checklist-progress-bar");
  const label  = container.querySelector(".checklist-progress-label");
  if (bar)   { bar.style.width = pct + "%"; bar.setAttribute("aria-valuenow", pct); }
  if (label) label.textContent = `${done}/${total} completed`;
}

/* ── Color palette swatches ─────────────────────────────────── */
function renderSwatches(value, container) {
  container.innerHTML = "";
  (value || "").split(",").forEach(hex => {
    hex = hex.trim();
    if (/^#[0-9a-fA-F]{3,6}$/.test(hex)) {
      const s = document.createElement("span");
      s.className = "color-swatch";
      s.style.background = hex;
      s.title = hex;
      container.appendChild(s);
    }
  });
}
