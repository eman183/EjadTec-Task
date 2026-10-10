/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

const REFRESH_INTERVAL = 3000;

publicWidget.registry.RealtimeRop = publicWidget.Widget.extend({
    selector: ".o_realtime_rop",
    events: {
        "click .o_realtime_rop_update": "_onUpdateClick",
        "submit .o_realtime_rop_form": "_onUpdateSubmit",
    },

    start() {
        this.grid = this.el.querySelector(".o_realtime_rop_grid");
        this.empty = this.el.querySelector(".o_realtime_rop_empty");
        this.status = this.el.querySelector(".o_realtime_rop_status");
        this.modalEl = this.el.querySelector(".o_realtime_rop_modal");
        this.form = this.el.querySelector(".o_realtime_rop_form");
        this.modalError = this.el.querySelector(".o_realtime_rop_modal_error");
        this.quantities = new Map();
        this.el.querySelectorAll(".o_realtime_rop_item").forEach((item) => {
            const qty = item.querySelector(".o_realtime_rop_qty span").textContent.trim();
            this.quantities.set(Number(item.dataset.productId), qty);
        });
        this.timer = setInterval(() => this._refresh(), REFRESH_INTERVAL);
        return this._super(...arguments);
    },

    destroy() {
        clearInterval(this.timer);
        this._super(...arguments);
    },

    async _refresh() {
        if (document.hidden) {
            return;
        }
        let products;
        try {
            products = await jsonrpc("/shop/realtime-rop/data", {});
        } catch {
            this._setStatus(false);
            return;
        }
        this._setStatus(true);
        this._render(products);
    },

    _onUpdateClick(ev) {
        const button = ev.currentTarget;
        this.form.product_id.value = button.dataset.productId;
        this.form.quantity.value = "";
        this.el.querySelector(".o_realtime_rop_modal_name").textContent = button.dataset.productName;
        this.el.querySelector(".o_realtime_rop_modal_qty").textContent = button.dataset.qty;
        this.modalError.classList.add("d-none");
        Modal.getOrCreateInstance(this.modalEl).show();
        this.modalEl.addEventListener("shown.bs.modal", () => this.form.quantity.focus(), { once: true });
    },

    async _onUpdateSubmit(ev) {
        ev.preventDefault();
        const submit = this.form.querySelector("[type=submit]");
        submit.disabled = true;
        let result;
        try {
            result = await jsonrpc("/rop-product/update/json", {
                product_id: this.form.product_id.value,
                quantity: this.form.quantity.value,
            });
        } catch {
            result = { success: false, error: "Could not reach the server. Please try again." };
        } finally {
            submit.disabled = false;
        }
        if (!result.success) {
            this.modalError.textContent = result.error;
            this.modalError.classList.remove("d-none");
            return;
        }
        Modal.getOrCreateInstance(this.modalEl).hide();
        this._refresh();
    },

    _setStatus(online) {
        this.status.classList.toggle("text-bg-success", online);
        this.status.classList.toggle("text-bg-danger", !online);
        this.status.lastChild.textContent = online ? " Live" : " Offline";
    },

    _render(products) {
        const previous = this.quantities;
        this.quantities = new Map();
        this.grid.replaceChildren(
            ...products.map((product) => {
                const qty = product.qty_available;
                const card = this._renderCard(product);
                const old = previous.get(product.id);
                if (old !== undefined && old !== qty) {
                    card.querySelector(".card").classList.add("border-warning", "border-2");
                }
                this.quantities.set(product.id, qty);
                return card;
            })
        );
        this.empty.classList.toggle("d-none", products.length > 0);
    },

    _renderCard(product) {
        const col = document.createElement("div");
        col.className = "col-6 col-md-4 col-lg-3 mb-4 o_realtime_rop_item";
        col.dataset.productId = product.id;
        col.innerHTML = `
            <div class="card h-100 shadow-sm">
                <a><img class="card-img-top p-3" style="height: 200px; object-fit: contain;"/></a>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title"><a class="text-decoration-none"></a></h6>
                    <div class="mt-auto">
                        <span class="text-muted small">Quantity on hand</span>
                        <div class="h4 mb-1 o_realtime_rop_qty"><span></span>
                            <small class="text-muted fs-6"></small></div>
                        <span class="text-muted small o_realtime_rop_point"></span>
                        <button type="button" class="btn btn-primary btn-sm w-100 mt-2 o_realtime_rop_update">
                            Update Product Quantity
                        </button>
                    </div>
                </div>
            </div>`;
        const [imageLink, titleLink] = col.querySelectorAll("a");
        imageLink.href = titleLink.href = product.website_url;
        const img = col.querySelector("img");
        img.src = product.image_url;
        img.alt = product.name;
        titleLink.textContent = product.name;
        col.querySelector(".o_realtime_rop_qty span").textContent = product.qty_available;
        col.querySelector(".o_realtime_rop_qty small").textContent = product.uom;
        col.querySelector(".o_realtime_rop_point").textContent = `Reorder point: ${product.rop_count}`;
        Object.assign(col.querySelector(".o_realtime_rop_update").dataset, {
            productId: product.id,
            productName: product.name,
            qty: product.qty_available,
        });
        return col;
    },
});

export default publicWidget.registry.RealtimeRop;
