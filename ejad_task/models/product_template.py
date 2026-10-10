# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import  ValidationError,UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_rop = fields.Boolean(
        string='Has ROP',
        default=False,
        help='Enable this option if this product uses a Re-Order Point.'
    )

    rop_count = fields.Integer(
        string='ROP Count',
        default=0,
        help='Minimum stock quantity before the product needs replenishment.'
    )

    rop_product_count = fields.Integer(
        string='ROP Products',
        compute='_compute_rop_product_count',
    )

    below_rop = fields.Boolean(
        string='Below ROP',
        compute='_compute_below_rop',
        store=True
    )


    @api.depends('has_rop','rop_count','qty_available')
    def _compute_below_rop(self):
        for product in self:
            product.below_rop = (
                    product.has_rop
                    and product.qty_available < product.rop_count
            )

    @api.depends('has_rop','rop_count')
    def _compute_rop_product_count(self):
        for product in self:

            domain = [
                ('has_rop', '=', True),
                ('rop_count','=', product.rop_count),

            ]


            # if product.id:
            #     domain.append(('id', '!=', product.id))

            product.rop_product_count = self.search_count(domain)

    @api.constrains('rop_count', 'has_rop')
    def _check_rop_count(self):
        for product in self:
            if product.has_rop and product.rop_count < 0:
                raise ValidationError(_(
                    'ROP Count cannot be negative.'
                ))

    def action_view_rop_products(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'ROP Products',
            'res_model': 'product.template',
            'view_mode': 'tree,form,kanban',
            'domain': [
                ('has_rop', '=', True),
                ('rop_count', '=', self.rop_count)

            ],
            'context': {
                'default_has_rop': True,
                'rop_count' : self.rop_count

            },
        }

    def action_update_rop_quantity(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Update Product Quantity"),
            "res_model": "rop.update.quantity.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_product_tmpl_id": self.id,
            },
        }




class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _notify_rop_update(self, product, location, quantity):
        groups = (
            self.env.ref('base.group_system')
            | self.env.ref('stock.group_stock_manager')
            | self.env.ref('stock.group_stock_user')
        )
        partners = groups.sudo().users.filtered(
            lambda user: user.active and user != self.env.user
        ).partner_id
        if not partners:
            return False

        message = _(
            '%(user)s updated the quantity on hand of %(product)s '
            'to %(quantity)s at %(location)s.',
            user=self.env.user.name,
            product=product.display_name,
            quantity=quantity,
            location=location.display_name,
        )
        product.product_tmpl_id.message_post(
            body=message,
            subject=_('Product quantity updated'),
            partner_ids=partners.ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        # Users whose preference is "By Email" get nothing in Odoo when no
        # mail server is configured, so also push a live notification.
        Bus = self.env['bus.bus'].sudo()
        for partner in partners:
            Bus._sendone(partner, 'simple_notification', {
                'type': 'warning',
                'title': _('Product quantity updated'),
                'message': message,
                'sticky': True,
            })
        return True


    POS_ROP_MIN_QTY = 5

    @api.model
    def action_notify_rop_admin(self, product_id):
        product = self.browse(product_id).exists()

        if not product:
            raise UserError(_("Product not found."))

        template = product.product_tmpl_id

        if not template.has_rop:
            return False

        available_stock = product.qty_available
        rop_count = template.rop_count

        if available_stock >= rop_count:
            return False

        admins = self.env.ref(
            'stock.group_stock_manager'
        ).users

        if not admins:
            return False

        activity_type = self.env.ref(
            'mail.mail_activity_data_todo'
        )

        model_id = self.env['ir.model']._get_id(
            'product.template'
        )
        for admin in admins:
            existing = self.env['mail.activity'].search([
                ('res_model_id', '=', model_id),
                ('res_id', '=', template.id),
                ('user_id', '=', admin.id),
                ('activity_type_id', '=', activity_type.id),
                ('summary', '=', 'Check Re-Order Point'),
            ], limit=1)

            if existing:
                continue

            self.env['mail.activity'].create({
                'res_model_id': model_id,
                'res_id': template.id,
                'user_id': admin.id,
                'activity_type_id': activity_type.id,
                'summary': 'Check Re-Order Point',
                'note': _(
                    'Product: %(product)s<br/>'
                    'Available stock: %(stock)s<br/>'
                    'Re-Order Point: %(rop)s<br/>'
                    'Please check stock and arrange replenishment if needed.',
                    product=product.display_name,
                    stock=available_stock,
                    rop=rop_count,
                ),
            })

        return True

