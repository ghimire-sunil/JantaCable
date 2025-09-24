from odoo import fields, models

class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    mobile_app_ok = fields.Boolean("Mobile App")

class ProductInherit(models.Model):
    _inherit = "product.product"

    mobile_app_ok = fields.Boolean("Mobile App", related="product_tmpl_id.mobile_app_ok")