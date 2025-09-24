from odoo import models, fields, api
from datetime import timedelta, datetime, time

class RouteSchedule(models.Model):
    _name = 'user.route.schedule'
    _inherit = ['mail.thread']
    
    
    user_id = fields.Many2one(
        string="User",
        comodel_name='res.users',
        required=True,
        tracking=True,
    )
    route_id = fields.Many2one(
        string="Route",
        comodel_name="partner.route",
        tracking=True,
        required=True   
    )
    date = fields.Date(
        string="Date",
        required=True,
        tracking=True,
    )

    # # recurrence fields
    # recurring_route = fields.Boolean(string="Recurrent")
    # recurring_count = fields.Integer(string="Routes in Recurrence", compute='_compute_recurring_count')
    # recurrence_id = fields.Many2one('route.schedule.recurrence', copy=False)
    # repeat_interval = fields.Integer(string='Repeat Every', default=1, compute='_compute_repeat', compute_sudo=True, readonly=False)
    # repeat_unit = fields.Selection([
    #     ('day', 'Days'),
    #     ('week', 'Weeks'),
    #     ('month', 'Months'),
    #     ('year', 'Years'),
    # ], default='week', compute='_compute_repeat', compute_sudo=True, readonly=False)
    # repeat_type = fields.Selection([
    #     ('forever', 'Forever'),
    #     ('until', 'Until'),
    # ], default="forever", string="Until", compute='_compute_repeat', compute_sudo=True, readonly=False)
    # repeat_until = fields.Date(string="End Date", compute='_compute_repeat', compute_sudo=True, readonly=False)

    # @api.model
    # def _get_recurrence_fields(self):
    #     return [
    #         'repeat_interval',
    #         'repeat_unit',
    #         'repeat_type',
    #         'repeat_until',
    #     ]

    # def _is_recurrence_valid(self):
    #     self.ensure_one()
    #     return self.repeat_interval > 0 and\
    #             (self.repeat_type != 'until' or self.repeat_until and self.repeat_until > fields.Date.today())

    # @api.depends('recurring_route')
    # def _compute_repeat(self):
    #     rec_fields = self._get_recurrence_fields()
    #     defaults = self.default_get(rec_fields)
    #     for route in self:
    #         for f in rec_fields:
    #             if route.recurrence_id:
    #                 route[f] = route.recurrence_id.sudo()[f]
    #             else:
    #                 if route.recurring_route:
    #                     route[f] = defaults.get(f)
    #                 else:
    #                     route[f] = False

    # @api.depends('recurrence_id')
    # def _compute_recurring_count(self):
    #     self.recurring_count = 0
    #     recurring_routes = self.filtered(lambda l: l.recurrence_id)
    #     count = self.env['user.route.schedule']._read_group([('recurrence_id', 'in', recurring_routes.recurrence_id.ids)], ['recurrence_id'], ['__count'])
    #     routes_count = {recurrence.id: count for recurrence, count in count}
    #     for route in recurring_routes:
    #         route.recurring_count = routes_count.get(route.recurrence_id.id, 0)

    # def _load_records_create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('recurring_route'):
    #             if not vals.get('recurrence_id'):
    #                 default_val = self.default_get(self._get_recurrence_fields())
    #                 vals.update(**default_val)
    #         route_id = vals.get('route_id')
    #         if route_id:
    #             self = self.with_context(default_route_id=route_id)
    #     routes = super()._load_records_create(vals_list)

    # @api.model_create_multi
    # def create(self,vals_list):
    #     res = super().create(vals_list)
    #     for vals in vals_list:
    #         # recurrence
    #         rec_fields = vals.keys() & self._get_recurrence_fields()
    #         if rec_fields and vals.get('recurring_route') is True:
    #             rec_values = {rec_field: vals[rec_field] for rec_field in rec_fields}
    #             recurrence = self.env['route.schedule.recurrence'].create(rec_values)
    #             vals['recurrence_id'] = recurrence.id
    #     return res

    # def write(self,vals):
    #     res = super().write(vals)
    #     # recurrence fields
    #     rec_fields = vals.keys() & self._get_recurrence_fields()
    #     if rec_fields:
    #         rec_values = {rec_field: vals[rec_field] for rec_field in rec_fields}
    #         for route in self:
    #             if route.recurrence_id:
    #                 route.recurrence_id.write(rec_values)
    #             elif vals.get('recurring_route'):
    #                 recurrence = self.env['route.schedule.recurrence'].create(rec_values)
    #                 route.recurrence_id = recurrence.id

    #     if not vals.get('recurring_route', True) and self.recurrence_id:
    #         routes_in_recurrence = self.recurrence_id.route_ids
    #         self.recurrence_id.unlink()
    #         routes_in_recurrence.write({'recurring_route': False})

    #     return res

    # @api.model
    # def default_get(self, default_fields):
    #     res = super().default_get(default_fields)
    #     if 'repeat_until' in default_fields:
    #         res['repeat_until'] = fields.Date.today() + timedelta(days=7)
    #     return res


    # def action_recurring_routes(self):
    #     return {
    #         'name': _('Routes in Recurrence'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'user.route.schedule',
    #         'view_mode': 'list,form',
    #         'context': {'create': False},
    #         'domain': [('recurrence_id', 'in', self.recurrence_id.ids)],
    #     }

    # # def action_project_sharing_recurring_tasks(self):
    # #     self.ensure_one()
    # #     recurrent_tasks = self.env['user.route.schedule'].search([('recurrence_id', 'in', self.recurrence_id.ids)])
    # #     # If all the recurrent tasks are in the same project, open the list view in sharing mode.
    # #     if recurrent_routes.route_id == self.route_id:
    # #         action = self.env['ir.actions.act_window']._for_xml_id('project.project_sharing_project_task_recurring_tasks_action')
    # #         action.update({
    # #             'context': {'default_project_id': self.project_id.id},
    # #             'domain': [
    # #                 ('project_id', '=', self.project_id.id),
    # #                 ('recurrence_id', 'in', self.recurrence_id.ids)
    # #             ]
    # #         })
    # #         return action
    # #     # If at least one recurrent task belong to another project, open the portal page
    # #     return {
    # #         'name': 'Portal Recurrent Tasks',
    # #         'type': 'ir.actions.act_url',
    # #         'url':  f'/my/projects/{self.project_id.id}/task/{self.id}/recurrent_tasks',
    # #     }

    # def action_unlink_recurrence(self):
    #     self.recurrence_id.route_ids.recurring_route = False
    #     self.recurrence_id.unlink()
    