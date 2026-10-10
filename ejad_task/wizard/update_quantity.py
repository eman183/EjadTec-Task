
from odoo import fields, models, _
from odoo.exceptions import UserError


class RopUpdateQuantityWizard(models.TransientModel):
    _name = "rop.update.quantity.wizard"
    _description = "Update Product Quantity"

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        readonly=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product Variant",
        required=True,
    )

    location_id = fields.Many2one(
        "stock.location",
        string="Warehouse Location",
        required=True,
        domain=[("usage", "=", "internal")],
    )

    quantity = fields.Integer(
        string="New Quantity on Hand",
        required=True,
        default=0,
    )

    def action_apply_quantity(self):
        self.ensure_one()

        if self.quantity < 0:
            raise UserError(_("Quantity cannot be negative."))

        if self.location_id.usage != "internal":
            raise UserError(
                _("Please select an internal stock location.")
            )

        Quant = self.env["stock.quant"].with_company(
            self.env.company
        )

        quant = Quant.search([
            ("product_id", "=", self.product_id.id),
            ("location_id", "=", self.location_id.id),
            ("lot_id", "=", False),
            ("package_id", "=", False),
            ("owner_id", "=", False),
        ], limit=1)

        if not quant:
            quant = Quant.create({
                "product_id": self.product_id.id,
                "location_id": self.location_id.id,
                "inventory_quantity": self.quantity,
            })
        else:
            quant.inventory_quantity = self.quantity

        # Apply the inventory adjustment through Odoo.
        quant.action_apply_inventory()

        self.env["product.product"]._notify_rop_update(
            self.product_id,
            self.location_id,
            self.quantity,
        )

        return {"type": "ir.actions.act_window_close"}