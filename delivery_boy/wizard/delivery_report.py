# -*- coding utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DispatchReport(models.TransientModel):
    _name = 'delivery_boy.delivery_report'
    _description = 'Print Delivery Report'

    delivery_person = fields.Many2one('res.users',string='Delivery Person', required=True, domain="[('is_delivery_person','=','true')]")
    start_date = fields.Date('From', required=True)
    end_date = fields.Date('To', required=True)

    
    def print_report(self):
        start_date = self.start_date
        end_date = self.end_date
        # product_id = self.product_id
        report_data = self.env['delivery_boy.picking'].search(
            [('schedule_date', '>=', start_date), ('schedule_date', '<=', end_date),('assigned','=',self.delivery_person.id),('state','=','completed')])
        if not report_data:
            raise ValidationError('No Dispatch data found please select appropriate date interval')
        datas = {
            'form':{
                'start_date':start_date,
                'end_date':end_date,
                'delivery_person':self.delivery_person.id,
                'name':self.delivery_person.name
            }
        }
        # return self.env['web'].get_action(self, 'vehicle_entry.dispatch_report', data=datas)
        return self.env.ref('delivery_boy.action_delivery_report').report_action(self, data=datas)
