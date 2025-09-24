from odoo import http
from odoo.http import content_disposition, request
import io
import xlwt
import xlsxwriter
import logging 
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import nepali_datetime



_logger = logging.getLogger(__name__)


class AuditLogController(http.Controller):

    @http.route('/audit_log/excel_report/<model("audit.log.wizard"):wizard>', type='http',  auth="user", csrf=False)
    def download_sales_report(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition',
                    content_disposition(str(wizard.start_date) + ' - ' + str(wizard.end_date) + ' - ' + 'Audit Log Report.xlsx'))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        


        nepali_start_date = nepali_datetime.date.from_datetime_date(wizard.start_date)
        nepali_end_date = nepali_datetime.date.from_datetime_date(wizard.end_date)
        nepali_start_date_str = f"{nepali_start_date.year}-{nepali_start_date.month:02d}-{nepali_start_date.day:02d}"
        nepali_end_date_str = f"{nepali_end_date.year}-{nepali_end_date.month:02d}-{nepali_end_date.day:02d}"

        new_start_date = datetime.combine(wizard.start_date, datetime.min.time())
        new_end_date = datetime.combine(wizard.end_date, datetime.max.time())- timedelta(minutes=1)
   
        header_style = workbook.add_format(
            {'font_name': 'Calibri','font_size': 8, 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        datetime_format = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left','num_format': 'yyyy-mm-dd hh:mm:ss'})
        date_format =workbook.add_format({
            'font_name': 'Times',
            'left': 1,
            'bottom': 1,
            'right': 1,
            'top': 1,
            'align': 'left'
        })


        sheet = workbook.add_worksheet("AUDIT LOG REPORT")
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        sheet.set_column('A:A', 25)
        sheet.set_column('B:F', 15)
        sheet.set_column('G:H', 20)
        sheet.write(
            0, 2, 'AUDIT LOG REPORT', header_style)
        
        # row 2
        sheet.write(1, 0, 'Company Name', header_style)
        sheet.write(1, 1, wizard.company_id.name, header_style)

        sheet.write(2, 0, 'Start Date', header_style)
        sheet.write(2, 1, nepali_start_date_str, date_format)
    
        sheet.write(3, 0, 'End Date', header_style)
        sheet.write(3, 1, nepali_end_date_str, date_format)


        # row 3
        sheet.write(4, 0, 'Created on (B.S. )', header_style)
        sheet.write(4, 1, 'Created on (A.D.)', header_style)
        sheet.write(4, 2, 'User', header_style)
        sheet.write(4, 3, 'Name', header_style)
        sheet.write(4, 4, 'Description', header_style)
        sheet.write(4, 5, 'New value Text', header_style)
        sheet.write(4, 6, 'Old value Text', header_style)
        sheet.write(4, 7, 'Session', header_style)
        sheet.write(4, 8, 'HTTP Request', header_style)
        sheet.write(4, 9, 'Technical name', header_style)
        sheet.write(4, 10, 'Method', header_style)


        
        audit_logs = wizard.env['auditlog.log.line.view'].search([('create_date', '>=', new_start_date), ('create_date', '<=', new_end_date)])


        row = 5
        for audit_log in audit_logs:
            sheet.write(row, 0, audit_log.nepali_date, datetime_format)
            sheet.write(row, 1, audit_log.create_date, datetime_format)
            sheet.write(row, 2, audit_log.user_id.name, text_style)
            sheet.write(row, 3, audit_log.name, text_style)
            sheet.write(row, 4, audit_log.field_description, text_style)
            sheet.write(row, 7, audit_log.http_session_id.display_name, text_style)
            sheet.write(row, 8, audit_log.http_request_id.name, text_style)
            sheet.write(row, 9, audit_log.field_name, text_style)
            sheet.write(row, 10, audit_log.method, text_style)
            if audit_log.new_value_text == False:
                sheet.write(row, 5, "", text_style)
            else:
                sheet.write(row, 5, audit_log.new_value_text, text_style)
            
            if audit_log.old_value_text == False:
                sheet.write(row, 6, "", text_style)
            else:
                sheet.write(row, 6, audit_log.old_value_text, text_style)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response