/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.pos.get_order();
        const partner = order.get_partner();

        if (!partner) {
            this.env.services.dialog.add(ConfirmationDialog, {
                title: "Customer Required",
                body: "Please select a customer before proceeding to payment.",
                confirmLabel: "OK",
                confirm: () => {
                },
            });
            return;
        }

        const phone = (partner.phone || "").trim();

        if (!phone) {
            this.env.services.dialog.add(ConfirmationDialog, {
                title: "Phone Number Required",
                body: "The selected customer does not have a phone number. Please add the customer's phone number.",
                confirmLabel: "OK",
                confirm: () => {
                },
            });
            return;
        }

        if (!phone.startsWith("+2")) {
            this.env.services.dialog.add(ConfirmationDialog, {
                title: "Invalid Phone Number",
                body: "The customer's phone number must start with +2. ",
                confirmLabel: "OK",
                confirm: () => {
                },
            });
            return;
        }

        return super.validateOrder(...arguments);
    }


});