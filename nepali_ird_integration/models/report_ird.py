# -*- coding: utf-8 -*-

from odoo import models, fields,api 
from datetime import date
import time
import odoo
import nepali_datetime
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class ReportIrd(models.AbstractModel):
    _name = 'report.ird_report.report_ird'

    def get_ird_report(self, docs):
       
        if docs.from_date and docs.to_date:
            rec = self.env['account.move'].search([
                                                        ('invoice_date', '>=', docs.from_date),('invoice_date', '<=', docs.to_date),('move_type','in',('out_invoice','out_refund'))])
        elif docs.from_date:
            rec = self.env['account.move'].search([
                                                        ('invoice_date', '>=', docs.from_date),('move_type','in',('out_invoice','out_refund'))])
        elif docs.to_date:
            rec = self.env['account.move'].search([
                                                            ('invoice_date', '<=', docs.to_date),('move_type','in',('out_invoice','out_refund'))])
        records = []
        # total = 0
        for r in rec:
            vals = {
                    'fy':r.fy_prefix,
                    'number': r.name,
                    'vat': r.partner_id.vat,
                    'name': r.partner_id.name,
                    'amount_untaxed': r.amount_untaxed,
                    'amount_discount': "0.00",
                    'amount_total': r.amount_total,
                    'amount_tax': r.amount_tax,
                    'bill_post': r.bill_post,
                    'printed_count': r.printed_count,
                    'last_printed': r.last_printed,
                    'user_id': r.user_id.name,
                    'move_type': r.move_type,
                    'state': r.state,
                    'date': r.date,
                    'is_realtime': r.is_realtime,
                    }
            records.append(vals)
        return [records]

    @api.model
    def _get_report_values(self, docids, data=None):
        """we are overwriting this function because we need to show values from other models in the report
        we pass the objects in the docargs dictionary"""
        active_model = self.env.context.get('active_model')
        docs = self.env[active_model].browse(self.env.context.get('active_id'))  
        datas = self.get_ird_report(docs)
        version_info = odoo.service.common.exp_version()
        k = version_info.get('server_version')
        j = version_info.get('server_version_info')
    
        if docs.from_date and docs.to_date:
            period = "From " + str(docs.from_date) + " To " + str(docs.to_date)
        elif docs.from_date:
            period = "From " + str(docs.from_date)
        elif docs.from_date:
            period = " To " + str(docs.to_date)
        return {
               'doc_ids': docids,
               'doc_model': active_model,
               'docs': docs,
               'time': time,
               'result': datas,
               'period': period,
               
            }
    

class IrdReport(models.TransientModel):
    _name = "ird.report"

    from_date = fields.Date('Start Date', required=True, default=date.today())
    to_date = fields.Date('End date', required=True, default=date.today())
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def print_ird_report(self):
        """Redirects to the report with the values obtained from the wizard
        'data['form']': name of employee and the date duration"""
        # data = {
        #     'start_date': self.from_date,
        #     'end_date': self.to_date,
        # }
        if self.from_date and self.to_date:
            rec = self.env['account.move'].search([
                                                        ('invoice_date', '>=', self.from_date),('invoice_date', '<=', self.to_date),('move_type','in',('out_invoice','out_refund'))])
        elif self.from_date:
            rec = self.env['account.move'].search([
                                                        ('invoice_date', '>=', self.from_date),('move_type','in',('out_invoice','out_refund'))])
        elif self.to_date:
            rec = self.env['account.move'].search([
                                                            ('invoice_date', '<=', self.to_date),('move_type','in',('out_invoice','out_refund'))])
            
        data = {'data':[]}
        # total = 0
        for r in rec:
            nepali_date = str(nepali_datetime.date.from_datetime_date(r.date)) if r.date else ''
            vals = {
                    'fy':r.fy_prefix,
                    'number': r.name,
                    'vat': r.partner_id.vat,
                    'name': r.partner_id.name,
                    'amount_untaxed': r.amount_untaxed,
                    'amount_discount': "0.00",
                    'amount_total': r.amount_total,
                    'amount_tax': r.amount_tax,
                    'bill_post': r.bill_post,
                    'printed_count': r.printed_count,
                    'last_printed': r.last_printed,
                    'user_id': r.user_id.name,
                    'move_type': r.move_type,
                    'state': r.state,
                    'date': r.date,
                    'is_realtime': r.is_realtime,
                    'nepali_date': r.nepali_date,
                    }
            data['data'].append(vals)
        # raise UserError(data)
        return self.env.ref('nepali_ird_integration.action_report_print_ird').report_action(self, data=data)
        # return [records]


        raise UserError(str(data))



    def get_excel_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/materialized_report/excel_report/%s' % (self.id),
            'target': 'new',
        }
