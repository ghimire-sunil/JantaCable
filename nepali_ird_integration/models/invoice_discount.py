from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def _get_reconciled_info_JSON_values(self):
        self.ensure_one()
        reconciled_vals = []
        for (
            partial,
            amount,
            counterpart_line,
        ) in self._get_reconciled_invoices_partials()[0]:
            reconciled_vals.append(
                self._get_reconciled_vals(partial, amount, counterpart_line)
            )
        return reconciled_vals
