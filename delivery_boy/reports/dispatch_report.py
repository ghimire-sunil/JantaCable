# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import ValidationError,UserError

class ReportDeliveryReport(models.AbstractModel):
    _name = 'report.delivery_boy.delivery_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        
        #Take the data between the selected date and vehicle's state is checkout
        form = data['form']
        report_data = self.env['delivery_boy.picking'].search(
            [('schedule_date', '>=', form['start_date']), ('schedule_date', '<=', form['end_date']),('assigned','=',form['delivery_person']),('state','=','completed')])
      
        
        return {
            'doc_ids': self.ids,
            'doc_model':'delivery_boy.delivery_report' ,
            'docs': report_data,
            'data': data,
        }

class ReportPaymentReport(models.AbstractModel):
    _name = 'report.delivery_boy.payment_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        
        #Take the data between the selected date and vehicle's state is checkout
        form = data['form']
       
        domain = [('payment_date', '>=', form['start_date']), ('payment_date', '<=', form['end_date']),('collected_by','in',form['delivery_person']),('state','!=','draft')]
        if len(form['delivery_person']) == 0:
            domain = [('payment_date', '>=', form['start_date']), ('payment_date', '<=', form['end_date']),('state','!=','draft')]
        
        report_data = self.env['delivery_boy.payment'].search(domain)
        
        total = 0
        verified=0
        pending =0

        for payment in report_data:
            amount = payment.amount
            if payment.state =='posted':
                verified +=amount
            else:
                pending += amount
            total +=amount
      
        return {
            'doc_ids': self.ids,
            'doc_model':'delivery_boy.payment_report' ,
            'docs': report_data,
            'extra':{
                'total':total,
                'verified':verified,
                'pending':pending
            },
            'data': data,
        }
