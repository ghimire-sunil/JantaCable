from odoo import models, fields
from datetime import date, datetime, timedelta

import nepali_datetime

class SaleWizard(models.TransientModel):
    _name = 'ng.salebook.wizard'
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date", default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    type = fields.Selection(selection=[
        ('out_invoice', 'Sales Book'),
        ('in_invoice', 'Purchase Book'),
        ('sales_report', 'Sales Book Report'),
        ('sales_pm_report', 'Sales Report With Payment Mode'),
        ('purchase_report', 'Purchase Book Report'),
        ('sales_return', 'Sales Return'),
        ('purchase_return', 'Purchase Return'),
    ])

    def get_excel_report(self):
        # redirect to /sale/excel_report controller to generate the excel file
        return {
            'type': 'ir.actions.act_url',
            'url': '/sale/excel_report/%s' % (self.id),
            'target': 'new',
        }
    
    


class AnnexReportWizard(models.TransientModel):
    _name = 'ng.annexreport.wizard'
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date", default=fields.Date.context_today)

    type = fields.Selection(selection=[
        ('annex_report', 'Annex Report'),
        ('vat_summary', 'VAT Summary'),
        ('tds_report', 'TDS Report')
    ])

    def get_excel_report(self):
        # redirect to /sale/excel_report controller to generate the excel file
        return {
            'type': 'ir.actions.act_url',
            'url': '/annex/excel_report/%s' % (self.id),
            'target': 'new',
        }


class AuditLogWizard(models.TransientModel):
    _name = 'audit.log.wizard'
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date", default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)


    def get_excel_report(self):
        # redirect to /sale/excel_report controller to generate the excel file
        return {
            'type': 'ir.actions.act_url',
            'url': '/audit_log/excel_report/%s' % (self.id),
            'target': 'new',
        }
