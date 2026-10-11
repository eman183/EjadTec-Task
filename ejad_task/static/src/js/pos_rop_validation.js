/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {Order} from "@point_of_sale/app/store/models";
import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog"
import {_t} from "@web/core/l10n/translation";

patch(Order.prototype, {

    async pay() {
        if (await this.checkRopBeforePayment()) {
            return super.pay();
        }
    },

    async checkRopBeforePayment() {
        const orderedQty = new Map();
        for (const line of this.get_orderlines()) {
            const product = line.get_product();
            if (!product.has_rop) {
                continue;
            }
            const entry = orderedQty.get(product.id) || {product, qty: 0};
            entry.qty += line.get_quantity();
            orderedQty.set(product.id, entry);
        }
        if (!orderedQty.size) {
            return true;
        }

        const stock = new Map();
        try {
            const records = await this.env.services.orm.read(
                "product.product",
                [...orderedQty.keys()],
                ["qty_available"]
            );
            for (const record of records) {
                stock.set(record.id, record.qty_available);
            }
        } catch {
        }

        const belowRop = [];
        for (const {product, qty} of orderedQty.values()) {
            const onHand = stock.has(product.id) ? stock.get(product.id) : product.qty_available;
            const remaining = onHand - qty;
            if (typeof onHand === "number" && remaining < product.rop_count) {
                belowRop.push({product, onHand, qty, remaining});
            }
        }
        if (!belowRop.length) {
            return true;
        }

        for (const {product, qty} of belowRop) {
            try {
                await this.env.services.orm.call(
                    "product.product",
                    "action_notify_rop_admin",
                    [product.id, qty]
                );
            } catch (error) {
                console.error("Failed to notify warehouse administrators:", error);
            }
        }

        const details = belowRop.map(({product, onHand, qty, remaining}) =>
            _t(
                "%(product)s: on hand %(onHand)s, ordered %(qty)s, remaining %(remaining)s, re-order point %(rop)s",
                {
                    product: product.display_name,
                    onHand,
                    qty,
                    remaining,
                    rop: product.rop_count,
                }
            )
        );
        this.env.services.dialog.add(AlertDialog, {
            title: _t("Below Re-Order Point"),
            body: _t("This order takes these products below their Re-Order Point:") +
                "\n" + details.join("\n"),
        });
        return false;
    },

});
