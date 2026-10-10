/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {Order} from "@point_of_sale/app/store/models";
import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog"
import {_t} from "@web/core/l10n/translation";

patch(Order.prototype, {


    async pay() {
        const order = this;
        const orderLines = order.get_orderlines();

        for (const line of orderLines) {
            const product = line.get_product();
            if (!product.has_rop) {
                continue;
            }
            const availableStock = product.qty_available;
            const ropCount = product.rop_count;
            console.log("ropCount",ropCount)
            console.log("availableStock",availableStock)

            if (
                typeof availableStock === "number" &&
                availableStock < ropCount
            ) {

                try {
                    await this.env.services.orm.call(
                        "product.product",
                        "action_notify_rop_admin",
                        [product.id]
                    );
                } catch (error) {
                    console.error(
                        "Failed to notify warehouse administrators:",
                        error
                    );
                }
                this.env.services.dialog.add(AlertDialog, {
                    body: _t("This product under of the Re-Order Point measure"),
                });

                return;
            }
        }

        return super.pay();
    },


});