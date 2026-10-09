/** @odoo-module **/

import {ProductScreen} from "@point_of_sale/app/screens/product_screen/product_screen";
import {usePos} from "@point_of_sale/app/store/pos_hook";
import {useService} from "@web/core/utils/hooks";
import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";

export class CashNowButton extends Component {
    static template = "ejad_task.CashNowButton";

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
    }

    async onClick() {
        const order = this.pos.get_order();
        if (!order || !order.get_orderlines().length) {
            this.notification.add(_t("Please add at least one product to the order."), {type: "warning"});
            return;
        }

        const configured = this.pos.config.default_customer_id;
        const customerId = Array.isArray(configured) ? configured[0] : configured;
        if (!customerId) {
            this.notification.add(_t("Please configure the Admin Customer in POS Configuration."), {type: "danger"});
            return;
        }

        let partner = this.pos.db.get_partner_by_id(customerId);
        if (!partner) {
            await this.pos._loadPartners([customerId]);
            partner = this.pos.db.get_partner_by_id(customerId);
        }
        if (!partner) {
            this.notification.add(_t("The Admin Customer is not available in this POS."), {type: "danger"});
            return;
        }

        const cashMethod = this.pos.payment_methods.find((method) => method.is_cash_count);
        if (!cashMethod) {
            this.notification.add(_t("No cash payment method is configured for this POS."), {type: "danger"});
            return;
        }

        order.set_partner(partner);
        order.paymentlines.filter((line) => line.payment_method).forEach((line) => order.remove_paymentline(line));
        order.add_paymentline(cashMethod);
        order.set_to_invoice(true);
        this.pos.showScreen("PaymentScreen");

        this.notification.add(_t("Customer %s selected.", partner.name), {type: "success"});
    }
}

ProductScreen.addControlButton({
    component: CashNowButton,
});