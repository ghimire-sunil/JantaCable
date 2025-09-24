from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    amount_discount = fields.Monetary(
        string="Discount",
        compute="_compute_purchase_discount",
        store=True,
        readonly=True,
        currency_field="currency_id",
        tracking=True,
    )
    taxed_amount_discount = fields.Monetary(
        string="Discount",
        compute="_compute_purchase_discount",
        store=True,
        readonly=True,
        currency_field="currency_id",
        tracking=True,
    )

    @api.depends(
        "order_line.price_unit",
        "order_line.product_qty",
    )
    def _compute_purchase_discount(self):
        for order in self:
            discount_total = 0.0
            for line in order.order_line:
                if line.product_id:
                    line_total = line.price_unit * line.product_qty
                    discount_value = (line.discount / 100.0) * line_total
                    discount_total += discount_value
            order.amount_discount = discount_total

    def action_open_discount_wizard(self):
        self.ensure_one()
        return {
            "name": _("Discount"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.order.discount",
            "view_mode": "form",
            "target": "new",
        }
