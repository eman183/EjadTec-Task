/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";

/**
 * Return true when the customer can be used for payment, otherwise show
 * the reason in a dialog and return false.
 */
export function checkCustomerPhone(partner, dialog) {
    const showError = (title, body) =>
        dialog.add(ConfirmationDialog, {title, body, confirmLabel: "OK", confirm: () => {}});

    if (!partner) {
        showError("Customer Required", "Please select a customer before proceeding to payment.");
        return false;
    }
    const phone = (partner.phone || "").trim();
    if (!phone) {
        showError(
            "Phone Number Required",
            "The selected customer does not have a phone number. Please add the customer's phone number."
        );
        return false;
    }
    if (!phone.startsWith("+2")) {
        showError("Invalid Phone Number", "The customer's phone number must start with +2. ");
        return false;
    }
    return true;
}

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const partner = this.pos.get_order().get_partner();
        if (!checkCustomerPhone(partner, this.env.services.dialog)) {
            return;
        }
        return super.validateOrder(...arguments);
    }
});
