from odoo import _, models, api, fields


class AccountInvoice(models.Model):
    _inherit = "account.move"

    amount_discount = fields.Monetary(
        string="Discount",
        readonly=True,
        compute="_compute_discount_amount",
    )

    def _compute_discount_amount(self):
        for move in self:
            total_discount_amount = 0.0
            for line in move.invoice_line_ids:
                if line.tax_ids:
                    if line.tax_ids[0].price_include_override == "tax_included":
                        total_discount_amount += line.discount_amount / 1.13
                    else:
                        total_discount_amount += line.discount_amount
                else:
                    total_discount_amount += line.discount_amount
            # Update the move's total discount
            move.amount_discount = total_discount_amount

    @api.depends(
        "invoice_line_ids.discount",
        "invoice_line_ids.quantity",
        "invoice_line_ids.price_unit",
    )
    def _compute_amount(self):
        return super()._compute_amount()

    def action_open_discount_wizard(self):
        self.ensure_one()
        return {
            "name": _("Discount"),
            "type": "ir.actions.act_window",
            "res_model": "account.move.discount",
            "view_mode": "form",
            "target": "new",
        }


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    discount_amount = fields.Monetary(
        string="Discount Amount", compute="_compute_discount_amount_currency"
    )

    price_subtotal_without_discount = fields.Monetary(
        string="Subtotal Without Discount",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("discount")
    def _compute_discount_amount_currency(self):
        for rec in self:
            if rec.discount:
                line_total = rec.price_unit * rec.quantity
                rec.discount_amount = (rec.discount / 100.0) * line_total
            else:
                rec.discount_amount = 0.00

    @api.depends("quantity", "discount", "price_unit", "tax_ids", "currency_id")
    def _compute_totals(self):
        resp = super()._compute_totals()
        for line in self:
            line.price_subtotal_without_discount = (
                line.price_subtotal + line.discount_amount
            )

        return resp
