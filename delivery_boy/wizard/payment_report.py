# -*- coding utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DispatchReport(models.TransientModel):
    _name = 'delivery_boy.payment_report'
    _description = 'Print Payment Report'

    delivery_person = fields.Many2many('res.users',string='Delivery Persons',domain="[('is_delivery_person','=','true')]")
    start_date = fields.Date('From', required=True)
    end_date = fields.Date('To', required=True)

    
    def print_report(self):
        start_date = self.start_date
        end_date = self.end_date
        # product_id = self.product_id
        domain = [('create_date', '>=', start_date), ('create_date', '<=', end_date),('state','!=','draft')]
        if self.delivery_person:
            domain = [('payment_date', '>=', start_date), ('payment_date', '<=', end_date),('collected_by','in',self.delivery_person.ids),('state','!=','draft')] 
        report_data = self.env['delivery_boy.payment'].search(domain=domain)
        if not report_data:
            raise ValidationError('No Payment data found please select appropriate date interval')
    
        datas = {
            'form':{
                'start_date':start_date,
                'end_date':end_date,
                'delivery_person':self.delivery_person.ids,
            }
        }
        return self.env.ref('delivery_boy.action_payment_report').report_action(self, data=datas)
