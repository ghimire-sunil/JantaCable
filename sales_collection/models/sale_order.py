# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from pytz import timezone
import datetime

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    date_order = fields.Datetime(related='order_id.date_order')
    