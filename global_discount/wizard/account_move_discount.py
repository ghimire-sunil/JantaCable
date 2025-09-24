from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveDiscount(models.TransientModel):
    _name = "account.move.discount"
    _description = "Discount Wizard"

    move_id = fields.Many2one(
        comodel_name="account.move",
        default=lambda self: self.env.context.get("active_id"),
        required=True,
    )
    company_id = fields.Many2one(related="move_id.company_id")
    currency_id = fields.Many2one(related="move_id.currency_id")
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
        order = self.move_id
        order.invoice_line_ids.write({"discount": 0})
        if self.discount_type == "pol_discount":
            order.invoice_line_ids.write({"discount": self.discount_percentage * 100})
        elif self.discount_type == "amount":
            total = sum(
                line.price_subtotal
                for line in order.invoice_line_ids
                if line.product_id
            )
            computed_percent = (self.discount_amount / total * 100.0) if total else 0.0
            order.invoice_line_ids.write({"discount": computed_percent})
        else:
            order.invoice_line_ids.write(
                {"discount": self.discount_percentage * 100 or 0.0}
            )
