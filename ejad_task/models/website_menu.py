# -*- coding: utf-8 -*-

from odoo import models


WAREHOUSE_MENU_URLS = ('/shop/rop-products', '/shop/realtime-rop')


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    def _compute_visible(self):
        super()._compute_visible()
        user = self.env.user
        if (
            user.has_group('stock.group_stock_manager')
            or user.has_group('stock.group_stock_user')
        ):
            return
        for menu in self:
            if menu.url in WAREHOUSE_MENU_URLS:
                menu.is_visible = False
