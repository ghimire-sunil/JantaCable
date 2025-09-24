from odoo import fields, models


class PartnerLocation(models.Model):
    _name = "partner.location"

    date = fields.Datetime(string="Date")
    latitude = fields.Float("Latitude", digits=(10, 7))
    longitude = fields.Float("Longitude", digits=(10, 7))
    partner_id = fields.Many2one("res.partner", "Contact")
