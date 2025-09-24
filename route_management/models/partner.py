from odoo import fields,models


class Partner(models.Model):
    _inherit = "res.partner"
    
    route_id = fields.Many2one(
        comodel_name="partner.route",
        string="Route",
        tracking=True,
    )
    outlet_type = fields.Many2one(
        comodel_name="outlet.type",
        string="Outlet Type",
        tracking=True,
    )
