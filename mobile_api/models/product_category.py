from odoo import fields, models

class ProductCategoryInherited(models.Model):
    _inherit = 'product.category'

    logo = fields.Binary("Company Logo")
    mobile_app_ok = fields.Boolean("Mobile App")