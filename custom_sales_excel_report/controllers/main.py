# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from datetime import datetime, timedelta
import nepali_datetime
from collections import defaultdict

class SalesExcellReport(http.Controller):
    @http.route('/custom_excell_report/sale_excel_report/<model("sale.report.wizard"):wizard>', type='http', auth="user", csrf=False)
    def get_sale_excel_report(self, wizard=None, **args):
        """
        Controller to generate Sale Excel reports based on the wizard data.
        """
        # Call the function to fetch attendance data
        sale_data = wizard.get_sales_report_data()

        eng_date = wizard.date_selected
        nep_date = nepali_datetime.date.from_datetime_date(eng_date)
        nepali_date_str = nep_date.strftime("%d %B, %Y")
        title_date = f"Date: {nepali_date_str} ({eng_date.strftime('%d %B')})"
        nepali_date_str_close = nep_date.strftime("%d")
        closing_till = f"Net Sales till {nepali_date_str_close}th"
        eng_date_prev = eng_date - timedelta(days=1)
        nep_date_prev = nepali_datetime.date.from_datetime_date(eng_date_prev)
        nepali_date_str_open = nep_date_prev.strftime("%d")
        open_till = f"Net Sales till {nepali_date_str_open}th"

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Sales Report')

        # Formatting
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        header_green = workbook.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1, 'align': 'center'})
        header_orange = workbook.add_format({'bg_color': '#FBE4D5', 'bold': True, 'border': 1, 'align': 'center'})
        header_yellow = workbook.add_format({'bg_color': '#FFF2CC', 'bold': True, 'border': 1, 'align': 'center'})
        center = workbook.add_format({'align': 'center'})
        number = workbook.add_format({'num_format': '#,##0.00'})
        center_yellow = workbook.add_format({'align': 'center','num_format': '#,##0.00','bg_color': '#FFF2CC'})
        number_yellow = workbook.add_format({'num_format': '#,##0.00','bg_color': '#FFF2CC'})

        # Set column widths
        sheet.set_column('A:A', 20)  # Product
        sheet.set_column('B:B', 8)   # Unit
        sheet.set_column('C:L', 12)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 20)
        sheet.set_column('L:L', 20)
        sheet.set_column('M:M', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('J:J', 20)

        # Title
        sheet.merge_range('A1:O1', 'Brij Himalayan Spring Pvt. Ltd.', bold)
        sheet.merge_range('A2:O2', 'Product wise Net Sales', bold)
        sheet.merge_range('A3:O3', title_date, bold)

        # Header Rows
        sheet.merge_range('A4:A5', 'Product', header_green)
        sheet.merge_range('B4:B5', 'Unit', header_green)
        sheet.merge_range('C4:D4', open_till, header_green)
        sheet.merge_range('E4:F4', 'Sales', header_green)
        sheet.merge_range('G4:H4', 'Sales Return', header_green)
        sheet.merge_range('I4:J4', 'Net Sales', header_green)
        sheet.merge_range('K4:K5', 'Net Rate', header_green)
        sheet.merge_range('L4:M4', closing_till, header_green)
        sheet.merge_range('N4:N5', 'Net Rate (per case)', header_green)
        sheet.merge_range('O4:O5', 'Net Rate (per ltr)', header_green)

        sheet.write('C5', 'Qty', header_green)
        sheet.write('D5', 'Amount', header_green)
        sheet.write('E5', 'Qty', header_green)
        sheet.write('F5', 'Amount', header_green)
        sheet.write('G5', 'Qty', header_green)
        sheet.write('H5', 'Amount', header_green)
        sheet.write('I5', 'Qty', header_green)
        sheet.write('J5', 'Amount', header_green)
        sheet.write('L5', 'Qty', header_green)
        sheet.write('M5', 'Amount', header_green)

        category_groups = defaultdict(list)
        for d in sale_data:
            category_groups[d['category_name']].append(d)
        
        row = 5
        # Grand totals
        grand_open_aty = grand_open_amt = grand_today_sale_qty = grand_today_sale_amt = 0
        grand_today_return_qty = grand_today_return_amt = 0
        grand_today_net_sale_qty = grand_today_net_sale_amt = 0
        grand_closing_sale_qty = grand_closing_sale_amt = 0

        for category, rows in category_groups.items():
            sheet.write(row, 0, f"Category: {category}", header_orange)
            row += 1

            # Fill Data
            open_aty = open_amt = today_sale_qty = today_sale_amt = today_return_qty = today_return_amt = 0
            today_net_sale_qty = today_net_sale_amt = 0
            closing_sale_qty = closing_sale_amt = 0

            for d in rows:
                open_aty += d['open_aty']
                open_amt += d['open_amt']
                today_sale_qty += d['today_sale_qty']
                today_sale_amt += d['today_sale_amt']
                today_return_qty += d['today_return_qty']
                today_return_amt += d['today_return_amt']
                today_net_sale_qty += d['today_net_sale_qty']
                today_net_sale_amt += d['today_net_sale_amt']
                closing_sale_qty += d['closing_sale_qty']
                closing_sale_amt += d['closing_sale_amt']

                # Grand totals
                grand_open_aty += d['open_aty']
                grand_open_amt += d['open_amt']
                grand_today_sale_qty += d['today_sale_qty']
                grand_today_sale_amt += d['today_sale_amt']
                grand_today_return_qty += d['today_return_qty']
                grand_today_return_amt += d['today_return_amt']
                grand_today_net_sale_qty += d['today_net_sale_qty']
                grand_today_net_sale_amt += d['today_net_sale_amt']
                grand_closing_sale_qty += d['closing_sale_qty']
                grand_closing_sale_amt += d['closing_sale_amt']

                sheet.write(row, 0, d['prod_name'], center)
                sheet.write(row, 1, d['unit'], center)

                sheet.write(row, 2, d['open_aty'], center)  # Net Sales till 15th - Qty
                sheet.write(row, 3, d['open_amt'], number)  # Net Sales till 15th - Amount

                sheet.write(row, 4, d['today_sale_qty'], center)  # Sales - Qty
                sheet.write(row, 5, d['today_sale_amt'], number)  # Sales - Amount

                sheet.write(row, 6, d['today_return_qty'], center)  # Sales Return - Qty
                sheet.write(row, 7, d['today_return_amt'], number)  # Sales Return - Amount

                sheet.write(row, 8, d['today_net_sale_qty'], center)  # Net Sales - Qty
                sheet.write(row, 9, d['today_net_sale_amt'], number)  # Net Sales - Amount

                sheet.write(row, 10, d['unit_price'], number)  # Net Rate

                sheet.write(row, 11, d['closing_sale_qty'], center)  # Net Sales till 16th - Qty
                sheet.write(row, 12, d['closing_sale_amt'], number)  # Net Sales till 16th - Amount

                sheet.write(row, 13, d['unit_price'], number)  # Net Rate (per case)
                sheet.write(row, 14, d['unit_price']/12, number)  # Net Rate (per ltr)

                row += 1

            # Total Row
            sheet.write(row, 0, "Sub Total", header_yellow)
            sheet.write(row, 1, "",number_yellow)
            sheet.write_number(row, 2, open_aty, center_yellow)
            sheet.write_number(row, 3, open_amt, number_yellow)
            sheet.write_number(row, 4, today_sale_qty, center_yellow)
            sheet.write_number(row, 5, today_sale_amt, number_yellow)
            sheet.write_number(row, 6, today_return_qty, center_yellow)
            sheet.write_number(row, 7, today_return_amt, number_yellow)
            sheet.write_number(row, 8, today_net_sale_qty, center_yellow)
            sheet.write_number(row, 9, today_net_sale_amt, number_yellow)
            sheet.write_blank(row, 10, None, number_yellow)
            sheet.write_number(row, 11, closing_sale_qty, center_yellow)
            sheet.write_number(row, 12, closing_sale_amt, number_yellow)
            sheet.write_blank(row, 13, None, number_yellow)
            sheet.write_blank(row, 14, None, number_yellow)
            row += 2

        # Grand Total Row
        sheet.write(row, 0, "Grand Total", header_yellow)
        sheet.write(row, 1, "", number_yellow)
        sheet.write_number(row, 2, grand_open_aty, center_yellow)
        sheet.write_number(row, 3, grand_open_amt, number_yellow)
        sheet.write_number(row, 4, grand_today_sale_qty, center_yellow)
        sheet.write_number(row, 5, grand_today_sale_amt, number_yellow)
        sheet.write_number(row, 6, grand_today_return_qty, center_yellow)
        sheet.write_number(row, 7, grand_today_return_amt, number_yellow)
        sheet.write_number(row, 8, grand_today_net_sale_qty, center_yellow)
        sheet.write_number(row, 9, grand_today_net_sale_amt, number_yellow)
        sheet.write_blank(row, 10, None, number_yellow)
        sheet.write_number(row, 11, grand_closing_sale_qty, center_yellow)
        sheet.write_number(row, 12, grand_closing_sale_amt, number_yellow)
        sheet.write_blank(row, 13, None, number_yellow)
        sheet.write_blank(row, 14, None, number_yellow)
        row += 2

        # Total Liters
        # sheet.merge_range(row, 0, row, 9, "Total (Liters)(Till Y'day)", header_orange)
        # sheet.write_number(row, 10, total_ltr_till_15, number)
        # row += 1
        # sheet.merge_range(row, 0, row, 9, "Total (Liters)(Today)", header_orange)
        # sheet.write_number(row, 10, total_ltr_today, number)

        workbook.close()
        xlsx_data = output.getvalue()
        output.close()

        filename = f'Sales_Report_{eng_date}.xlsx'
        return request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={filename}')
            ]
        )

