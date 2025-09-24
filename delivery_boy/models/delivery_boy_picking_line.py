# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class DeliveryPicking(models.Model):
    _inherit = 'stock.move'

    price = fields.Float('Price Unit',related='sale_line_id.price_unit')



