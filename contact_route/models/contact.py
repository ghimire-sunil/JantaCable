from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    route_id = fields.Many2one(
        comodel_name="delivery.route",
        string="Route",
    )
