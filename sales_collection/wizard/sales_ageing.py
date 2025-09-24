from odoo import models, fields
from datetime import date,timedelta


class SaleAgeing(models.TransientModel):
    _name = 'sales.ageing.wizard'
    start_date = fields.Date("Start Date", default=fields.Date.context_today)
    end_date = fields.Date("End Date", default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    

    def get_sale_excel_report(self):
        # redirect to /sale/excel_report controller to generate the excel file
        return {
            'type': 'ir.actions.act_url',
            'url': '/sale/sales_ageing/%s' % (self.id),
            'target': 'new',
        }
    
    # def _compute_end_date(self):
    #     self.end_date = self.start_date+timedelta(days=7) if self.start_date else False