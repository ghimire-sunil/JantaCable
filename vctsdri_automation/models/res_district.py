from odoo import models, fields


class ResDistrict(models.Model):
    _name = "res.district"
    _description = "District"

    name = fields.Char(required=True, string="Name")
    code = fields.Integer(
        string="Code",
        required=True,
    )
    country_id = fields.Many2one("res.country", string="Country", required=True)
