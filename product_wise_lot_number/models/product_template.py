from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sequence_id = fields.Many2one(
        "ir.sequence", "Reference Sequence", check_company=True, copy=False
    )
