# -*- coding: utf-8 -*-

from odoo import models, fields, api


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

    @api.depends('has_rop', 'rop_count', 'qty_available')
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
                raise models.ValidationError(
                    'ROP Count cannot be negative.'
                )

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
