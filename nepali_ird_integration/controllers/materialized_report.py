from odoo import http
from odoo.http import content_disposition, request
import io
import xlwt
import xlsxwriter
import logging 
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from nepali_datetime import date as nepali_date


_logger = logging.getLogger(__name__)


class MaterializedReportController(http.Controller):
    @http.route('/materialized_report/excel_report/<model("ird.report"):wizard>', type='http',  auth="user", csrf=False)
    def download_materialized_report(self,wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition',
                    content_disposition('Materialized Report.xlsx'))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        start_date = datetime.combine(wizard.from_date, datetime.min.time())
        nep_date = nepali_date.from_datetime_date(wizard.from_date)
        nepali_start_date = nep_date.strftime('%Y-%m-%d')
        end_date = datetime.combine(wizard.to_date, datetime.max.time())- timedelta(minutes=1)
        nep_end_date = nepali_date.from_datetime_date(wizard.to_date)
        nepali_end_date = nep_end_date.strftime('%Y-%m-%d')

        header_style = workbook.add_format(
            {'font_name': 'Calibri','font_size': 8, 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        datetime_format = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left','num_format': 'yyyy-mm-dd hh:mm:ss'})

        sheet = workbook.add_worksheet("MATERIALIZED REPORT")
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        sheet.set_column('A:A', 25)
        sheet.set_column('B:F', 15)
        sheet.set_column('G:H', 20)
        sheet.write(
            0, 2, 'MATERIALIZED REPORT', header_style)
        sheet.write(1, 0, 'Company Name', header_style)
        sheet.write(1, 1, wizard.company_id.name, header_style)

        sheet.write(2, 0, 'Start Date', header_style)
        sheet.write(2, 1, nepali_start_date, datetime_format)

        sheet.write(3, 0, 'End Date', header_style)
        sheet.write(3, 1, nepali_end_date, datetime_format)

        sheet.write(4, 0, 'FY', header_style)
        sheet.write(4, 1, 'Inv no', header_style)
        sheet.write(4, 2, 'Inv Date', header_style)
        sheet.write(4, 3, 'Inv Date(B.S)', header_style)
        sheet.write(4, 4, 'Customer Name', header_style)
        sheet.write(4, 5, 'Pan', header_style)
        sheet.write(4, 6, 'Basic Amt', header_style)
        sheet.write(4, 7, 'Discount', header_style)
        sheet.write(4, 8, 'Taxable Amt', header_style)
        sheet.write(4, 9, 'Tax', header_style)
        sheet.write(4, 10, 'Total Amt', header_style)
        sheet.write(4, 11, 'Sync State', header_style)
        sheet.write(4, 12, 'Print State', header_style)
        sheet.write(4, 13, 'Active', header_style)
        sheet.write(4, 14, 'Last Printed', header_style)
        sheet.write(4, 15, 'Entered By', header_style)
        sheet.write(4, 16, 'Is realtime', header_style)
        sheet.write(4, 17, 'Printed By', header_style)
        sheet.write(4, 18, 'Payment Method', header_style)
        sheet.write(4, 19, 'VAT Refund Amount (if any)', header_style)
        sheet.write(4, 20, 'Transaction Amount (if any)', header_style)

        data = request.env['account.move'].search([('invoice_date', '>=', start_date),('invoice_date', '<=', end_date),('move_type','in',('out_invoice','out_refund'))])
        row = 5
        for rec in data:
            if rec.fy_prefix:
                sheet.write(row, 0, rec.fy_prefix, text_style)
            else:
                sheet.write(row, 0, "", text_style)
            sheet.write(row, 1, rec.name, text_style)
            sheet.write(row, 2 , rec.date, datetime_format)
            sheet.write(row, 3, rec.nepali_date, datetime_format)
            sheet.write(row, 4, rec.partner_id.name , text_style)
            if rec.partner_id.vat:
                sheet.write(row, 5, rec.partner_id.vat, text_style)
            else:
                sheet.write(row, 5, "", text_style)
            sheet.write(row, 6, rec.amount_untaxed, text_style)
            sheet.write(row, 7, "0.00", text_style)
            sheet.write(row, 8, rec.amount_untaxed, text_style)
            sheet.write(row, 9, rec.amount_tax, text_style)
            sheet.write(row, 10, rec.amount_total, text_style)
            if rec.bill_post:
                sheet.write(row, 11, "TRUE", text_style)
            else:
                sheet.write(row, 11, "FALSE", text_style)
            if rec.printed_count > 0:
                sheet.write(row, 12, "PRINTED", text_style)
            else:
                sheet.write(row, 12, "NOT PRINTED", text_style)
            if rec.printed_count > 0:
                sheet.write(row, 13, "ACTIVE", text_style)
            else:
                sheet.write(row, 13, "INACTIVE", text_style)
            sheet.write(row, 14, rec.last_printed, datetime_format)
            sheet.write(row, 15, rec.user_id.name, text_style)
            if rec.is_realtime:
                sheet.write(row, 16, "TRUE", text_style)
            else:
                sheet.write(row, 16, "FALSE", text_style)
            sheet.write(row, 17, request.env.user.name, text_style)
            sheet.write(row, 18, "", text_style)
            sheet.write(row, 19, "", text_style)
            sheet.write(row, 20,"", text_style)
            row += 1



        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response