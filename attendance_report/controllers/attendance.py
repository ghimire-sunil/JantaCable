# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from datetime import datetime
import nepali_datetime
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AttendanceExcelReportController(http.Controller):
    @http.route('/attendance/excel_report/<model("attendance.filter"):wizard>', type='http', auth="user", csrf=False)
    def get_attendance_excel_report(self, wizard=None, **args):
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition',
                    content_disposition('Attendance Report From - ' + str(wizard.from_date) + ' To - '+ str(wizard.to_date) + '.xlsx'))
                    
            ]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        initial_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 12, 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        background_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left', 'bg_color':'f8c088'})
        total_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center', 'bg_color':'f8c088'})

        sheet = workbook.add_worksheet("Attendance Report")
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        sheet.set_column('A:A', 25)
        sheet.set_column('B:F', 15)
        sheet.set_column('G:H', 20)
        sheet.write(
            0, 2, 'Personal Ledger', initial_style)

        employee = wizard.employee_ids
        for emp in employee:
            sheet.write('A2', f"Employee Name:{emp.name}", text_style)
            sheet.write('A3', f"Date Range: {wizard.from_date.strftime('%d/%m/%Y')} - {wizard.to_date.strftime('%d/%m/%Y')}", text_style)
            sheet.write('A4', f"Generated On: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response


        # """
        # Controller to generate attendance Excel reports based on the wizard data.
        # """
        # # Call the function to fetch attendance data
        # attendance_data = wizard.get_attendance_data()

        # # Extract necessary data from attendance_data
        # total = attendance_data['total']
        # recorded = attendance_data['recorded']
        # present_array = attendance_data['present_array']
        # absent_array = attendance_data['absent']
        # _logger.info(f" ahiufhiauehfuoiah: {recorded}")

        # # leave_array = attendance_data['leave_array']
        # # weekend_array = attendance_data['weekend_array']
        # # holiday_array = attendance_data['holiday_array']
        # attendance_records = attendance_data['attendance']
        

        # # Define the filename dynamically based on the date range
        # filename = f"Attendance_Report_{wizard.from_date}_{wizard.to_date}.xlsx"
        # response = request.make_response(
        #     None,
        #     headers=[
        #         ('Content-Type', 'application/vnd.ms-excel'),
        #         ('Content-Disposition', content_disposition(filename))
        #     ]
        # )

        # # Initialize an in-memory output stream for the Excel file
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # # Define styles for formatting
        # title_style = workbook.add_format({'font_size': 16, 'bold': True, 'align': 'center'})
        # header_style = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'border': 1})
        # text_style = workbook.add_format({'font_size': 10, 'align': 'left', 'border': 1})
        # number_style = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1})
        # summary_style = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'center', 'border': 1})
        # remarks_style = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1, 'font_color': 'red'})

        # # Create a worksheet
        # sheet = workbook.add_worksheet("Attendance Report")
        # sheet.set_landscape()
        # sheet.set_paper(9) 
        # sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        # # Title Row
        # sheet.merge_range('A1:F1', 'Attendance Report', title_style)
        # for emp in wizard.employee_ids:
        #     sheet.write('A2', f"Employee Name:{emp.name}", text_style)
        #     sheet.write('A3', f"Date Range: {wizard.from_date.strftime('%d/%m/%Y')} - {wizard.to_date.strftime('%d/%m/%Y')}", text_style)
        #     sheet.write('A4', f"Generated On: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", text_style)

        # # Attendance Summary Section
        #     summary_headers = ['Total Days', 'Recorded', 'Present' 'Absent']
        #     summary_data = [
        #         total,
        #         sum(recorded),
        #         sum(present_array),
        #         sum(absent_array),
                
        #         # sum(leave_array),
        #         # sum(holiday_array),
        #         # sum(weekend_array)
        #     ]
        #     _logger.info(f"kashfciauhfiuahe{summary_data}")


        #     for col_num, header in enumerate(summary_headers):
        #         sheet.write(4, col_num, header, header_style)
        #         sheet.write(5, col_num, summary_data[col_num], summary_style)

        #     # Attendance Details Section
        #     sheet.write(7, 0, 'Date', header_style)
        #     sheet.write(7, 1, 'Day', header_style)
        #     sheet.write(7, 2, 'Check-in', header_style)
        #     sheet.write(7, 3, 'Check-out', header_style)
        #     sheet.write(7, 4, 'Worked Hours', header_style)
        #     sheet.write(7, 5, 'Remarks', header_style)

        #     # Populate attendance details
        #     row = 8
        #     for employee_records in attendance_records:
        #         for record in employee_records:
        #             check_in_time = record.get('check_in', '').strftime('%H:%M:%S') if record.get('check_in') else ''
        #             check_out_time = record.get('check_out', '').strftime('%H:%M:%S') if record.get('check_out') else ''
        #             worked_hours = record.get('worked_hours', 0.0)
        #             remarks = record.get('remarks', '')

        #             # Write data to the sheet
        #             sheet.write(row, 0, record['date'].strftime('%Y-%m-%d'), text_style)
        #             sheet.write(row, 1, record['day'], text_style)
        #             sheet.write(row, 2, check_in_time, text_style)
        #             sheet.write(row, 3, check_out_time, text_style)
        #             sheet.write(row, 4, f"{worked_hours:.2f}", number_style)
        #             sheet.write(row, 5, remarks, remarks_style if remarks == 'Absent' else text_style)
        #             row += 1

        #     # Close the workbook and prepare the response
        #     workbook.close()
        #     output.seek(0)
        #     response.stream.write(output.read())
        #     output.close()

        #     return response
