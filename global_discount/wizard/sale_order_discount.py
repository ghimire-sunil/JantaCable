from odoo import models

from odoo.exceptions import UserError


class SaleOrderDiscount(models.TransientModel):
    _inherit = "sale.order.discount"

    def action_apply_discount(self):
        self.ensure_one()
        self = self.with_company(self.company_id)
        order = self.sale_order_id
        order.order_line.write({"discount": 0})
        if self.discount_type == "sol_discount":
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

        order._compute_sale_discount()
        order._compute_tax_totals()
