# -*- coding: utf-8 -*-
from odoo import fields, models


class Product(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(
        groups="hide_cost_price.groups_view_cost_price",
    )
