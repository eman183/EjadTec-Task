# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

import pytz

from odoo import fields, http
from odoo.exceptions import AccessError
from odoo.http import request


class EjadApiController(http.Controller):

    def _json(self, data, status=200):
        return request.make_json_response(data, status=status)

    def _error(self, message, status=400):
        return self._json({"error": message}, status=status)

    def _has_any_group(self, *xmlids):
        return any(request.env.user.has_group(xmlid) for xmlid in xmlids)

    def _check_pos_access(self):
        return self._has_any_group(
            "point_of_sale.group_pos_user",
            "point_of_sale.group_pos_manager",
        )

    def _check_stock_access(self):
        return self._has_any_group(
            "stock.group_stock_user",
            "stock.group_stock_manager",
        )

    def _parse_date(self, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def _to_utc(self, day, at_time):
        tz = pytz.timezone(request.env.user.tz or "UTC")
        local = tz.localize(datetime.combine(day, at_time))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _order_data(self, order):
        return {
            "id": order.id,
            "name": order.name,
            "pos_reference": order.pos_reference or "",
            "date_order": fields.Datetime.to_string(order.date_order),
            "session": {"id": order.session_id.id, "name": order.session_id.name},
            "customer": order.partner_id.name or "",
            "cashier": order.user_id.name or "",
            "state": order.state,
            "amount_tax": order.amount_tax,
            "amount_total": order.amount_total,
            "amount_paid": order.amount_paid,
            "currency": order.currency_id.name,
            "lines": [{
                "product_id": line.product_id.id,
                "product": line.product_id.display_name,
                "qty": line.qty,
                "price_unit": line.price_unit,
                "discount": line.discount,
                "price_subtotal_incl": line.price_subtotal_incl,
            } for line in order.lines],
        }

    def _product_data(self, product):
        return {
            "id": product.id,
            "name": product.display_name,
            "default_code": product.default_code or "",
            "quantity_on_hand": product.qty_available,
            "has_rop": product.has_rop,
            "rop_count": product.rop_count,
            "below_rop": product.qty_available < product.rop_count,
        }

    @http.route("/api/orders", type="http", auth="user",
                methods=["GET"], csrf=False)
    def orders_by_date(self, start_date=None, end_date=None, **kwargs):
        if not self._check_pos_access():
            return self._error("Access denied", 403)

        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        if not start or not end:
            return self._error(
                "start_date and end_date are required, format YYYY-MM-DD."
            )
        if start > end:
            return self._error("start_date must be before end_date.")

        orders = request.env["pos.order"].search([
            ("date_order", ">=", self._to_utc(start, time.min)),
            ("date_order", "<", self._to_utc(end + timedelta(days=1), time.min)),
        ], order="date_order")
        return self._json({
            "start_date": start_date,
            "end_date": end_date,
            "count": len(orders),
            "orders": [self._order_data(order) for order in orders],
        })

    @http.route("/api/rop-products", type="http", auth="user",
                methods=["GET"], csrf=False)
    def rop_count_products(self, **kwargs):
        if not self._check_stock_access():
            return self._error("Access denied", 403)

        products = request.env["product.template"].search([
            ("has_rop", "=", True),
            ("rop_count", ">", 0),
        ], order="name")
        return self._json({
            "count": len(products),
            "products": [self._product_data(product) for product in products],
        })

    @http.route("/api/rop-products/<int:product_id>", type="http",
                auth="user", methods=["POST", "PUT"], csrf=False)
    def set_rop_count(self, product_id, **kwargs):
        if not self._check_stock_access():
            return self._error("Access denied", 403)

        try:
            payload = request.get_json_data()
        except ValueError:
            payload = kwargs
        rop_count = (payload or {}).get("rop_count")
        if isinstance(rop_count, bool):
            rop_count = None
        try:
            rop_count = int(rop_count)
        except (TypeError, ValueError):
            return self._error("rop_count is required and must be an integer.")
        if rop_count < 0:
            return self._error("rop_count cannot be negative.")

        product = request.env["product.template"].browse(product_id).exists()
        if not product:
            return self._error("Product not found.", 404)

        try:
            product.write({"has_rop": True, "rop_count": rop_count})
        except AccessError:
            return self._error("You are not allowed to update products.", 403)
        return self._json({
            "success": True,
            "product": self._product_data(product),
        })

    @http.route("/api/pos-sessions/<int:session_id>/orders", type="http",
                auth="user", methods=["GET"], csrf=False)
    def session_orders(self, session_id, **kwargs):
        if not self._check_pos_access():
            return self._error("Access denied", 403)

        session = request.env["pos.session"].browse(session_id).exists()
        if not session:
            return self._error("POS session not found.", 404)

        orders = session.order_ids.sorted("date_order")
        return self._json({
            "session": {
                "id": session.id,
                "name": session.name,
                "pos": session.config_id.name,
                "state": session.state,
                "opened_by": session.user_id.name,
                "start_at": fields.Datetime.to_string(session.start_at),
                "stop_at": fields.Datetime.to_string(session.stop_at),
            },
            "count": len(orders),
            "total": sum(orders.mapped("amount_total")),
            "orders": [self._order_data(order) for order in orders],
        })
