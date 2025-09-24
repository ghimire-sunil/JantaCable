from odoo import fields, models
from datetime import date, timedelta

class RouteManagementScheduleWizard(models.TransientModel):
    _name = 'route.management.schedule.wizard'

    route_id = fields.Many2one(
        string="Route",
        comodel_name="partner.route" 
    )
    from_date = fields.Date('From', default=date.today(), required=True)
    to_date = fields.Date('To', default=date.today(), required=True)
    user_ids = fields.Many2many('res.users',string='Users')

    def action_create_scheduled_routes(self):
        dates = []

        delta = self.to_date - self.from_date
        for i in range(delta.days + 1):
            current_date = self.from_date + timedelta(days=i)
            dates.append(current_date)

        for user in self.user_ids:
            for d in dates:
                previous_dates = self.env['user.route.schedule'].sudo().search([('route_id','=',self.route_id.id), ('user_id','=',user.id),('date','=',d)])
                if previous_dates:
                    continue
                self.env['user.route.schedule'].sudo().create({
                    'route_id': self.route_id.id,
                    'user_id': user.id,
                    'date': d 
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }