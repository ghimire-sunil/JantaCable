from odoo import models, fields


class User(models.Model):
    _inherit = "res.users"

    role = fields.Selection(related="partner_id.role", readonly=False, store=True)
