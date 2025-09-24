from odoo import models, api, fields

class DistributorAchievementReport(models.Model):
    _name = "distributor.achievement.report"
    _description = "Distributor Achievement Report"
    _order = 'id'

    target_id = fields.Many2one('distributor.commission.plan.target', "Period", readonly=True)
    plan_id = fields.Many2one('distributor.commission.plan', "Commission Plan", readonly=True)
    user_id = fields.Many2one('res.users', "Sales Person", readonly=True)
    store_target = fields.Integer(string="Store Target")
    case_target = fields.Integer(string="Case Sales Target")
    achieved_store_target = fields.Float("Achieved Store Target", readonly=True)
    achieved_case_target = fields.Float("Achieved Case Target", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    date_to = fields.Date(string="Period", readonly=True)
