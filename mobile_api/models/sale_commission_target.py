from odoo import fields, models

class SalesCommissionTarget(models.Model):
    _inherit = "sale.commission.plan.target"

    store_target = fields.Integer(string="Store Visit Target")

class SalesCommissionReport(models.Model):
    _inherit = "sale.commission.report"    
    
    store_target = fields.Integer(string="Store Visit Target", related="target_id.store_target")