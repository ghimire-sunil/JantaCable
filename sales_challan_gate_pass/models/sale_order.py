# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from pytz import timezone
import datetime
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
        
    freight_amount = fields.Char(
        string='Freight Amount',
    )
    advance_amount = fields.Char(
        string='Advance Amount',
    )
    mls_number = fields.Char(
        string='MLS No.',
    )


    def _get_current_date_time(self):
        return datetime.datetime.now(timezone('Asia/Kathmandu')).strftime('%Y-%m-%d %I:%M %p')
    
    def print_sales_challan(self):
        return self.env.ref('sales_challan_gate_pass.action_report_sales_challan').report_action(self)
        