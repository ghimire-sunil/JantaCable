from odoo import models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _prepare_stock_lot_values(self):
        self.ensure_one()

        if self.product_id.sequence_id:
            name = self.product_id.sequence_id.next_by_id()
            exist_lot = not name or self.env["stock.lot"].search(
                [
                    ("product_id", "=", self.product_id.id),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", name),
                ],
                limit=1,
            )
            if exist_lot:
                name = self.env["stock.lot"]._get_next_serial(
                    self.company_id, self.product_id
                )
            if not name:
                raise UserError(
                    _("Please set the first Serial Number or a default sequence")
                )
            return {
                "product_id": self.product_id.id,
                "name": name,
            }

        return super()._prepare_stock_lot_values()
