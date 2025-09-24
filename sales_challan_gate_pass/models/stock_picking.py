# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from pytz import timezone
import datetime
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    vehicle_in_time = fields.Datetime('Vehicle In Time')
    vehicle_out_time = fields.Datetime('Vehicle Out Time')

    def _get_current_date_time(self):
        return datetime.datetime.now(timezone('Asia/Kathmandu')).strftime('%Y-%m-%d %I:%M %p')
    
    def print_gate_pass(self):
        return self.env.ref('sales_challan_gate_pass.action_report_gate_pass').report_action(self)
        