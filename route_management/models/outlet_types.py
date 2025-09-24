from odoo import fields, models

class OutletTypes(models.Model):
    _name = 'outlet.type'

    name = fields.Char()