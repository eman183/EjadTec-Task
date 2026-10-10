from odoo import http
from odoo.http import request


class RopProductController(http.Controller):

    @http.route(
        "/rop-product/json",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def get_rop_products(self, **kwargs):
        if not (
            request.env.user.has_group(
                "stock.group_stock_manager"
            )
            or request.env.user.has_group(
                "stock.group_stock_user"
            )
        ):
            return request.make_json_response(
                {"error": "Access denied"},
                status=403,
            )

        products = request.env["product.template"].search([
            ("type", "=", "product"),
            ("qty_available", "<", 5),
        ], order="name")

        result = []
        for product in products:
            result.append({
                "id": product.id,
                "name": product.display_name,
                "default_code": product.default_code or "",
                "quantity_on_hand": product.qty_available,
                "uom": product.uom_id.name,
                "has_rop": product.has_rop,
                "rop_count": product.rop_count,
                "below_rop": product.qty_available < product.rop_count,
            })

        return request.make_json_response({
            "count": len(result),
            "products": result,
        })