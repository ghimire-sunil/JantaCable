from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderDiscount(models.TransientModel):
    _name = "purchase.order.discount"
    _description = "Discount Wizard"

    purchase_order_id = fields.Many2one(
        "purchase.order",
        default=lambda self: self.env.context.get("active_id"),
        required=True,
    )
    company_id = fields.Many2one(related="purchase_order_id.company_id")
    currency_id = fields.Many2one(related="purchase_order_id.currency_id")
    discount_amount = fields.Monetary(string="Amount")
    discount_percentage = fields.Float(string="Percentage")
    discount_type = fields.Selection(
        selection=[
            ("pol_discount", "On All Order Lines"),
            ("po_discount", "Global Discount"),
            ("amount", "Fixed Amount"),
        ],
        default="amount",
    )

    @api.constrains("discount_type", "discount_percentage")
    def check_discount_amount(self):
        for wizard in self:
            if wizard.discount_type in ("pol_discount", "po_discount") and (
                wizard.discount_percentage > 1.0 or wizard.discount_percentage < 0.0
            ):
                raise ValidationError(_("Invalid discount amount"))

    def action_discount_apply(self):
        self.ensure_one()
        self = self.with_company(self.company_id)
        order = self.purchase_order_id
        order.order_line.write({"discount": 0})
        if self.discount_type == "pol_discount":
            order.order_line.write({"discount": self.discount_percentage * 100})
        elif self.discount_type == "amount":
            total = sum(
                line.product_qty * line.price_unit
                for line in order.order_line
                if line.product_id
            )
            computed_percent = (self.discount_amount / total * 100.0) if total else 0.0
            print(computed_percent)
            order.order_line.write({"discount": computed_percent})
        else:
            order.order_line.write({"discount": self.discount_percentage * 100 or 0.0})

        order._compute_purchase_discount()
        order._compute_tax_totals()
