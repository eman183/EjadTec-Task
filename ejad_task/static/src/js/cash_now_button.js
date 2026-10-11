/** @odoo-module **/

import {ProductScreen} from "@point_of_sale/app/screens/product_screen/product_screen";
import {usePos} from "@point_of_sale/app/store/pos_hook";
import {useService} from "@web/core/utils/hooks";
import {ConnectionLostError} from "@web/core/network/rpc_service";
import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {checkCustomerPhone} from "./payment_screen";

export class CashNowButton extends Component {
    static template = "ejad_task.CashNowButton";

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.ui = useService("ui");
        this.report = useService("report");
        this.hardwareProxy = useService("hardware_proxy");
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
        if (!checkCustomerPhone(partner, this.dialog)) {
            return;
        }

        const cashMethod = this.pos.payment_methods.find((method) => method.is_cash_count);
        if (!cashMethod) {
            this.notification.add(_t("No cash payment method is configured for this POS."), {type: "danger"});
            return;
        }

        if (!(await order.checkRopBeforePayment())) {
            return;
        }

        order.set_partner(partner);
        order.paymentlines.filter((line) => line.payment_method).forEach((line) => order.remove_paymentline(line));
        order.add_paymentline(cashMethod);
        order.set_to_invoice(true);

        if (this.pos.config.cash_rounding && !order.check_paymentlines_rounding()) {
            this.notification.add(_t("The payment amount does not respect the cash rounding."), {type: "danger"});
            return;
        }

        await this._validateOrder(order);
    }

    async _validateOrder(order) {
        this.hardwareProxy.openCashbox();
        order.date_order = luxon.DateTime.now();
        order.finalized = true;

        this.ui.block();
        let syncResult;
        try {
            syncResult = await this.pos.push_single_order(order);
            if (!syncResult) {
                order.finalized = false;
                return;
            }
            if (syncResult[0]?.account_move) {
                await this.report.doAction("account.account_invoices", [syncResult[0].account_move]);
            }
        } catch (error) {
            if (!(error instanceof ConnectionLostError)) {
                order.finalized = false;
                throw error;
            }
            // Offline: the order stays in the local queue and syncs later.
        } finally {
            this.ui.unblock();
        }

        this.pos.db.remove_unpaid_order(order);
        this.pos.showScreen("ReceiptScreen");
        this.notification.add(_t("Order paid in cash for %s.", order.get_partner().name), {type: "success"});
    }
}

ProductScreen.addControlButton({
    component: CashNowButton,
});
