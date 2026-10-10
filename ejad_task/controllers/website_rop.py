# -*- coding: utf-8 -*-
from odoo import _, http, tools
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute


class WebsiteRopController(http.Controller):

    def _check_rop_access(self):
        user = request.env.user
        allowed = (
            user.has_group("base.group_system")
            or user.has_group("stock.group_stock_manager")
            or user.has_group("stock.group_stock_user")
        )
        if not allowed:
            raise AccessError("You cannot access ROP products.")

    @http.route(
        ["/shop/rop-products", "/shop/rop-products/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def rop_products(self, page=0, **kwargs):
        self._check_rop_access()
        candidates = request.env["product.template"].search(
            request.website.sale_product_domain()
        )
        return self._render_rop_shop_page(
            candidates.filtered(
                lambda product: product.qty_available < product.rop_count
            ),
            url="/shop/rop-products",
            page=page,
            title=_("ROP Products"),
            subtitle=_("Products with quantity on hand below the reorder point."),
            empty_message=_("No products are currently below the reorder point."),
        )

    @http.route(
        ["/rop-product", "/rop-product/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def rop_product_below_five(self, page=0, **kwargs):
        self._check_rop_access()
        products = request.env["product.template"].search(
            request.website.sale_product_domain() + [
                ("type", "=", "product"),
                ("qty_available", "<", 5),
            ],
            order="name",
        )
        return self._render_rop_shop_page(
            products,
            url="/rop-product",
            page=page,
            title=_("ROP Product"),
            subtitle=_("Products with quantity on hand less than 5."),
            empty_message=_("No products currently have less than 5 units on hand."),
        )

    def _render_rop_shop_page(self, products_all, url, page,
                              title, subtitle, empty_message):
        website = request.website
        ppr = website.shop_ppr or 4
        ppg = len(products_all) or 1
        pager = website.pager(
            url=url,
            total=len(products_all),
            page=page,
            step=ppg,
            scope=5,
        )
        products = products_all[pager["offset"]:pager["offset"] + ppg]

        pricelist = website.pricelist_id
        fiscal_position = website.fiscal_position_id.sudo()
        products_prices = products._get_sales_prices(pricelist, fiscal_position)
        layout_mode = request.session.get("website_sale_shop_layout_mode") or "grid"
        empty_category = request.env["product.public.category"]

        return request.render("website_sale.products", {
            "search": "",
            "original_search": None,
            "order": "",
            "category": empty_category,
            "attrib_values": [],
            "attrib_set": set(),
            "pager": pager,
            "pricelist": pricelist,
            "fiscal_position": fiscal_position,
            "add_qty": 1,
            "products": products,
            "search_product": products_all,
            "search_count": len(products_all),
            "bins": TableCompute().process(products, ppg, ppr),
            "ppg": ppg,
            "ppr": ppr,
            "categories": empty_category,
            "attributes": request.env["product.attribute"],
            "keep": QueryURL(url),
            "search_categories_ids": [],
            "layout_mode": layout_mode,
            "products_prices": products_prices,
            "get_product_prices": lambda product: products_prices[product.id],
            "float_round": tools.float_round,
            "tags": set(),
            "all_tags": request.env["product.tag"],
            "min_price": 0.0,
            "max_price": 0.0,
            "available_min_price": 0.0,
            "available_max_price": 0.0,
            "rop_products_page": True,
            "rop_page_url": url,
            "rop_page_title": title,
            "rop_page_subtitle": subtitle,
            "rop_page_empty": empty_message,
        })

    def _get_realtime_rop_data(self):
        products = request.env["product.template"].search(
            request.website.sale_product_domain(), order="name"
        ).filtered(lambda product: product.qty_available > 5)
        return [{
            "id": product.id,
            "name": product.display_name,
            "qty_available": "%g" % product.qty_available,
            "uom": product.uom_id.name,
            "rop_count": product.rop_count,
            "image_url": f"/web/image/product.template/{product.id}/image_256",
            "website_url": product.website_url,
        } for product in products]

    @http.route(
        "/shop/realtime-rop",
        type="http",
        auth="user",
        website=True,
    )
    def realtime_rop(self, **kwargs):
        self._check_rop_access()
        return request.render(
            "ejad_task.website_realtime_rop_page",
            {"rop_products": self._get_realtime_rop_data()},
        )

    @http.route(
        "/shop/realtime-rop/data",
        type="json",
        auth="user",
        website=True,
    )
    def realtime_rop_data(self, **kwargs):
        self._check_rop_access()
        return self._get_realtime_rop_data()

    def _apply_rop_quantity(self, product_id, quantity):
        """Return an error message, or False when the quantity was applied."""
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            return _("Please enter a valid whole number.")
        if quantity < 0:
            return _("Quantity cannot be negative.")

        template = request.env["product.template"].browse(
            product_id
        ).exists()
        if not template or not template.sale_ok:
            return _("Product not found.")

        variants = template.product_variant_ids
        if len(variants) != 1:
            return _(
                "This product has several variants. "
                "Update it from the backend instead."
            )

        product = variants
        location = request.env["stock.location"].search([
            ("usage", "=", "internal"),
            ("company_id", "in", [
                request.env.company.id, False
            ]),
        ], order="company_id desc, id", limit=1)
        if not location:
            return _("No internal stock location found.")

        quant = request.env["stock.quant"].search([
            ("product_id", "=", product.id),
            ("location_id", "=", location.id),
            ("lot_id", "=", False),
            ("package_id", "=", False),
            ("owner_id", "=", False),
        ], limit=1)

        if not quant:
            quant = request.env["stock.quant"].create({
                "product_id": product.id,
                "location_id": location.id,
                "inventory_quantity": quantity,
            })
        else:
            quant.inventory_quantity = quantity

        quant.action_apply_inventory()

        request.env["product.product"]._notify_rop_update(
            product, location, quantity,
        )
        return False

    @http.route(
        "/rop-product/update",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def update_rop_product(self, product_id=None, quantity=None,
                           redirect=None, **kwargs):
        self._check_rop_access()
        self._apply_rop_quantity(product_id, quantity)
        if redirect not in ("/shop/rop-products", "/rop-product"):
            redirect = "/shop/rop-products"
        return request.redirect(redirect)

    @http.route(
        "/rop-product/update/json",
        type="json",
        auth="user",
        website=True,
    )
    def update_rop_product_json(self, product_id=None,
                                quantity=None, **kwargs):
        self._check_rop_access()
        error = self._apply_rop_quantity(product_id, quantity)
        return {"success": not error, "error": error or ""}