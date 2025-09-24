from odoo import _, api, Command, fields, exceptions, models
from dateutil.relativedelta import relativedelta
from datetime import date

class DistributorCommissionPlan(models.Model):
    _name = "distributor.commission.plan"
    _inherit = ['mail.thread']

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    name = fields.Char("Name", required=True)
    date_from = fields.Date("From", required=True, default=lambda self: fields.Date.today() + relativedelta(day=1, month=1), tracking=True)
    date_to = fields.Date("To", required=True, default=lambda self: fields.Date.today() + relativedelta(years=1, day=1, month=1) - relativedelta(days=1), tracking=True)
    target_ids = fields.One2many('distributor.commission.plan.target', 'plan_id', compute='_compute_targets',
        store=True, readonly=False)
    user_ids = fields.One2many('distributor.commission.plan.user', 'plan_id', copy=True)
    state = fields.Selection([('draft', "Draft"), ('approved', "Approved"), ('done', "Done"), ('cancel', "Cancelled")],
                             required=True, default='draft', tracking=True)
    
    @api.constrains('date_from', 'date_to')
    def _date_constraint(self):
        for plan in self:
            if not plan.date_to > plan.date_from:
                raise exceptions.ValidationError(_("The start date must be before the end date."))
            
    @api.model
    def _date2name(self, dt):
        return dt.strftime('%b %Y')
    
    @api.depends('date_from', 'date_to')
    def _compute_targets(self):
        for plan in self:
            if not plan.date_from or not plan.date_to:
                continue
            date_from = plan.date_from
            timedelta = relativedelta(months=1, day=1)
            date_from = date_from - relativedelta(days=1) + timedelta
            
            targets = [Command.clear()]
            while date_from + timedelta - relativedelta(days=1) <= plan.date_to:
                targets += [Command.create({
                    'name': self._date2name(date_from),
                    'date_from': date_from,
                    'date_to': date_from + timedelta - relativedelta(days=1)
                })]
                date_from += timedelta
            plan.target_ids = targets

    def action_approve(self):
        self.state = 'approved'

    def action_draft(self):
        self.state = 'draft'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    # @api.depends('user_ids.plan_id')
    # def _compute_commissions(self):
    #     for record in self:
    #         current_plan = self.env['']
    #         self.env['distributor_commission_report'].sudo().create({
    #             'plan_id': record.id,
    #             'target_id':
    #         })



    # def action_open_commission(self):
    #     self.ensure_one()
    #     return {
    #         "type": "ir.actions.act_window",
    #         "res_model": "sale.commission.report",
    #         "name": _("Related commissions"),
    #         "views": [[self.env.ref('sale_commission.sale_commission_report_view_list').id, "list"]],
    #         "domain": [('plan_id', '=', self.id)],
    #     }
    

class DistributorCommissionPlanTarget(models.Model):
    _name = "distributor.commission.plan.target"

    plan_id = fields.Many2one('distributor.commission.plan', ondelete='cascade')
    name = fields.Char("Period", required=True, readonly=True)
    date_from = fields.Date("From", required=True, readonly=True)
    date_to = fields.Date("To", required=True, readonly=True)
    store_target = fields.Integer(string="Store Target")
    case_target = fields.Integer(string="Case Sales Target")
        

class DistributorCommissionPlanUser(models.Model):
    _name = "distributor.commission.plan.user"

    plan_id = fields.Many2one('distributor.commission.plan', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', "Salesperson", required=True, domain="[('share', '=', False)]")

    date_from = fields.Date("From", compute='_compute_date_from', store=True, readonly=False)
    date_to = fields.Date("To")

    _sql_constraints = [
        ('user_uniq', 'unique (plan_id, user_id)', "The user is already present in the plan"),
    ]

    @api.constrains('date_from', 'date_to')
    def _date_constraint(self):
        for user in self:
            if user.date_to and user.date_from and user.date_to < user.date_from:
                raise exceptions.UserError(_("From must be before To"))
            if user.date_from and user.plan_id.date_from and user.date_from < user.plan_id.date_from:
                raise exceptions.UserError(_("User period cannot start before the plan."))
            if user.date_to and user.plan_id.date_to and user.date_to > user.plan_id.date_to:
                raise exceptions.UserError(_("User period cannot end after the plan."))
            
    @api.depends('plan_id')
    def _compute_date_from(self):
        today = fields.Date.today()
        for user in self:
            if user.date_from:
                return
            if not user.plan_id.date_from:
                return
            user.date_from = max(user.plan_id.date_from, today) if user.plan_id.state != 'draft' else user.plan_id.date_from

    # @api.depends('plan_id')
    # def _compute_targets(self):
    #     for record in self:
    #         print("hello")
    #         epoch_year = date.today().year
    #         print("yoooo")
    #         print(date(epoch_year, 12, 31))
    #         if record.plan_id.date_from >= date.today() and record.plan_id.date_to <= date(epoch_year, 12, 31):
    #             print("erm??")
    #             print(record._origin.plan_id)
    #             print("whattttttttttttttttttt")
    #             print(record.plan_id.target_ids)
    #         print(record._origin.plan_id)
    #         record.plan_id.target_ids = False
    #             # record.target_ids = record.plan_id.target_ids
    #             # record.target_ids = [(6, 0, [record.plan_id.target_ids])]