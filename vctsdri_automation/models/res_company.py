from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    district_id = fields.Many2one(
        string="District",
        comodel_name="res.district",
    )
