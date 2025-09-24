from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_discount = fields.Monetary(
        string="Discount",
        compute="_compute_sale_discount",
        store=True,
        readonly=True,
        currency_field="currency_id",
        tracking=True,
    )

    @api.depends(
        "order_line.price_unit",
        "order_line.product_uom_qty",
    )
    def _compute_sale_discount(self):
        for order in self:
            discount_total = 0.0
            for line in order.order_line:
                if line.product_id:
                    line_total = line.price_unit * line.product_uom_qty
                    discount_value = (line.discount / 100.0) * line_total
                    discount_total += discount_value
            order.amount_discount = discount_total
