from odoo import _, fields, models
import time

class DistributorAchievementWizard(models.TransientModel):
    _name = 'distributor.achievement.wizard'

    from_date = fields.Date('From', default=time.strftime('%Y-01-01'))
    to_date = fields.Date('To', default=time.strftime('%Y-12-31'))
    user_ids = fields.Many2many('res.users', 'Users')

    def action_open_window(self):
        self.ensure_one()

        all=self.env['distributor.achievement.report'].search([])
        for one in all:
            one.unlink()
        
        plans = self.env['distributor.commission.plan'].sudo().search([('state','=','approved'),('user_ids.user_id', 'in', self.user_ids.mapped('id')), ('date_from','>=',self.from_date), ('date_to', '<=', self.to_date)])

        context = dict(self.env.context, create=False, edit=False)

        def ref(xml_id):
            proxy = self.env['ir.model.data']
            return proxy._xmlid_lookup(xml_id)[1]

        tree_view_id = ref('mobile_api.distributor_achievement_report_view_list')
        pivot_view_id = ref('mobile_api.distributor_achievement_report_view_pivot')
        graph_view_id = ref('mobile_api.distributor_achievement_report_view_graph')

        context.update(user_ids=self.user_ids)
        if self.from_date:
            context.update(date_from=self.from_date)

        if self.to_date:
            context.update(date_to=self.to_date)

        views = [
            (tree_view_id, 'list'),
            (pivot_view_id, 'pivot'),
            (graph_view_id, 'graph')
        ]
        
        for plan in plans:
            for user in plan.user_ids:
                for target in plan.target_ids:
                    cases_sold = 0
                    lines = self.env['distributor.order.line'].sudo().search([('order_id.user_id','=',user.user_id.id), ('order_id.order_date', '>=', target.date_from), ('order_id.order_date','<=', target.date_to)])
                    for line in lines:
                        cases_sold += line.qty

                    self.env['distributor.achievement.report'].sudo().create({
                        'target_id': target.id,
                        'plan_id': plan.id,
                        'user_id': user.user_id.id,
                        'store_target': target.store_target,
                        'case_target': target.case_target,
                        'achieved_case_target': cases_sold,
                        'date_to': target.date_to
                    })

        return {
            'name': _('Distributor Achievement Report'),
            'context': context,
            'view_mode': 'list',
            'res_model': 'distributor.achievement.report',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'target': 'current'
        }