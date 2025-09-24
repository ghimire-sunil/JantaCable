from odoo import fields, models

class Discount(models.Model):
    _inherit = 'product.pricelist'

    default = fields.Boolean()