# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from datetime import timedelta, datetime, date, time
from odoo.exceptions import UserError


class SaleExcelReportController(http.Controller):
    @http.route([
        '/sale/sales_ageing/<model("sales.ageing.wizard"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_sale_excel_report(self, wizard=None, **args):
        # the wizard parameter is the primary key that odoo sent
        # with the get_excel_report method in the ng.sale.wizard model
        # contains salesperson, start date, and end date

        # create a response with a header in the form of an excel file
        # so the browser will immediately download it
        # The Content-Disposition header is the file name fill as needed

        # raise UserError(request.env.company_ids)

        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition',
                    content_disposition(str(wizard.start_date) + ' - ' + str(wizard.end_date) + ' Sales Collection Report.xlsx'))
            ]
        )


        # create workbook object from xlsxwriter library
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        start_date = datetime.combine(wizard.start_date, time.min)
        end_date = datetime.combine(wizard.end_date, time.max)

        # create some style to set up the font type, the font size, the border, and the aligment
        title_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 10, 'bold': True, 'align': 'center', 'bg_color': '#c5e0b4', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1,'valign': 'vcenter','text_wrap': True})
        border_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'font_size': 10, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 10, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'font_size': 10, 'bold': True, 'bottom': 1,'bg_color': '#ffe699', 'right': 1, 'top': 1, 'align': 'right'})
        initial_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 10,  'font_color': 'red', 'italic': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        right_style = workbook.add_format(
            {'font_name': 'Times', 'italic': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        blue_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 12, 'font_color': 'blue', 'underline':True, 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        dark_border_format = workbook.add_format({
            'border': 1,  # Thick border
            'border_color': 'black',  # Dark border color
        })
        
        # create worksheet/tab per salesperson
        sheet = workbook.add_worksheet("Sales Collection")
        # set the orientation to landscape
        sheet.set_landscape()
        # set up the paper size, 9 means A4
        sheet.set_paper(9)
        # set up the margin in inch
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        # set up the column width
        sheet.set_column('A:A', 12)
        sheet.set_column('B:C', 10)
        sheet.set_column('E:E', 0.5)
        sheet.set_row(0, 30) 
        sheet.set_row(1, 20) 
        sheet.set_row(2, 25) 


        # the report title
        # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
        sheet.merge_range('A1:A3','Product', title_style)
        sheet.merge_range('B1:B3','Unit', title_style)
        
        previous_fiscal_date = request.env['account.fiscal.year'].search([('date_to', '<=', date.today()),('date_from', '<=', date.today())],order='date_to DESC', limit=1)
        sheet.merge_range('C1:C3', f'FY {previous_fiscal_date.name}', title_style)
        if start_date.day == 1:
            sheet.merge_range('D1:D3', 'Previous Sales this Month', title_style)
        else:
            month_start_date = start_date.replace(day=1)
            month_end_date = start_date - timedelta(days=1)
            sheet.merge_range('D1:D3', f"Previous Sales this Month {month_start_date.strftime('%d/%m/%Y')} to {month_end_date.strftime('%d/%m/%Y')}", title_style)
        # sheet.merge_range('F2:K2', 'Current Week', title_style)
        # sheet.merge_range('L4:L5', 'Total sales  for 2nd Week', title_style)
        # sheet.merge_range('N1:N3', 'Total Net Sales (for month of Shrawan, 2082)', title_style)
        # sheet.merge_range('O1:O3', 'Total Sales till date', title_style)
        # ok=wizard.start_date.
        sheet.write(3, 0, 'Quantity', border_style)
        # sheet.write(0, 1, 'Unit', title_style)
        # sheet.write(0, 2, 'FY 2081-82', title_style)
        company = wizard.company_id
        # set date columns
        col = 5
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            day = current_date.day
            if 10 <= day % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
            sheet.write(2, col, f"{day}{suffix}", title_style)
            current_date += timedelta(days=1)
            col += 1
        sheet.set_column(col+1, col+1, 0.5)
        cell_start = xl_rowcol_to_cell(0, col+2)
        cell_end = xl_rowcol_to_cell(2, col+2)
        range = f'{cell_start}:{cell_end}'
        sheet.merge_range(range,'Total Net Sales this Month', title_style)
        cell_start = xl_rowcol_to_cell(0, col+3)  
        cell_end = xl_rowcol_to_cell(2, col+3)
        range = f'{cell_start}:{cell_end}'
        sheet.merge_range(range,'Total Sales till date', title_style)
        cell_start = xl_rowcol_to_cell(0, 5)  
        cell_end = xl_rowcol_to_cell(0, col)
        range = f'{cell_start}:{cell_end}'
        sheet.merge_range(range,'Current Week', title_style)
        cell_start = xl_rowcol_to_cell(1, col)  
        cell_end = xl_rowcol_to_cell(2, col)
        range = f'{cell_start}:{cell_end}'
        sheet.merge_range(range,'Total sales for this Week', title_style)
        cell_start = xl_rowcol_to_cell(1, 5)  
        cell_end = xl_rowcol_to_cell(1, col-1)
        range = f'{cell_start}:{cell_end}'
        month_date = start_date.strftime("%B")
        year_date = start_date.year
        sheet.merge_range(range,f'{month_date} {year_date}', title_style)
        
        
        uom_case = request.env['uom.uom'].search([('name', '=', 'CASE')],limit=1)
        case_product = request.env['product.product'].search([('uom_id', '=', uom_case.id)])
        uom_jar = request.env['uom.uom'].search([('name', '=', 'JAR')],limit=1)
        jar_product = request.env['product.product'].search([('uom_id', '=', uom_jar.id)])
        row = 4
        current_fiscal_date = request.env['account.fiscal.year'].search([('date_to', '>=', date.today()),('date_from', '<=', date.today())], limit=1)
        fiscal_total_liter=[]
        week_total_liter=[]
        last_week_liter=[]
        if case_product:
            for product in case_product:
                if '250ML' in product.name:
                    liter_uom = 6
                else:
                    liter_uom = 12
                product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale'), '&', ('date_order', '>=', current_fiscal_date.date_from), ('date_order', '<=', current_fiscal_date.date_to)])
                old_product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale'), '&', ('date_order', '>=', previous_fiscal_date.date_from), ('date_order', '<=', previous_fiscal_date.date_to)])
                total_quantity = sum(map(lambda x: float(x.product_uom_qty), old_product_order))
                previous_total_quantity_liter = sum(map(lambda x: float(x.product_uom_qty*liter_uom), old_product_order))
                week_total_quantity_liter = sum(map(lambda x: float(x.product_uom_qty*liter_uom), product_order))
                fiscal_total_liter.append(previous_total_quantity_liter)
                week_total_liter.append(week_total_quantity_liter)
                # last_week = product_order.filtered(
                #     lambda l: l.date_order >= start_date  and l.date_order <= end_date
                # )
                last_week = product_order.filtered(
                    lambda l: (
                    l.date_order.year == start_date.year and
                    l.date_order.month == start_date.month and
                    l.date_order < start_date
                ))
                last_week_total_quantity = sum(map(lambda x: float(x.product_uom_qty), last_week))
                last_week_total_liter = sum(map(lambda x: float(x.product_uom_qty*liter_uom), last_week))
                last_week_liter.append(last_week_total_liter)
                
                sheet.write(row, 0, product.name, text_style)
                sheet.write(row, 1, product.uom_id.name, text_style)
                sheet.write(row, 2, total_quantity, text_style)
                sheet.write(row, 3, last_week_total_quantity, text_style)
                
                col = 5
                for given_date in date_list:
                    day_products = product_order.filtered(
                    lambda l: l.date_order >= datetime.combine(given_date.date(), time.min)  and l.date_order <= datetime.combine(given_date.date(), time.max)
                    )
                    day_total_quantity = sum(map(lambda x: float(x.product_uom_qty), day_products))
                    sheet.write(row, col, day_total_quantity, text_style)
                    col += 1
                cell_start = xl_rowcol_to_cell(row, 5)  # E1
                cell_end = xl_rowcol_to_cell(row, col-1)
                sum_formula = f'=SUM({cell_start}:{cell_end})'
                sheet.write_formula(row, col, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 3)  # E1
                cell_end = xl_rowcol_to_cell(row, col)
                sum_formula = f'{cell_start}+{cell_end}'
                sheet.write_formula(row, col+2, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 2)  # E1
                cell_end = xl_rowcol_to_cell(row, col+2)
                sum_formula = f'={cell_start}+{cell_end}'
                sheet.write_formula(row, col+3, sum_formula, text_style)
                row += 1
            case_total_row = row
            sheet.write(row, 0, 'Sub Total (Case)', number_style)
            quantity_sum_start = xl_rowcol_to_cell(4, 2)
            quantity_sum_end = xl_rowcol_to_cell(row-1, 2)
            quantity_formula = f'=SUM({quantity_sum_start}:{quantity_sum_end})'
            sheet.write(row, 1, '', number_style)
            sheet.write_formula(row, 2, quantity_formula, number_style)
            fiscal_quantity_sum_start = xl_rowcol_to_cell(4, 3)
            fiscal_quantity_sum_end = xl_rowcol_to_cell(row-1, 3)
            fiscal_quantity_formula = f'=SUM({fiscal_quantity_sum_start}:{fiscal_quantity_sum_end})'
            sheet.write_formula(row, 3, fiscal_quantity_formula, number_style)
            col = 1
            while len(date_list) >= col:
                cell_start = xl_rowcol_to_cell(4, col+4)
                cell_end = xl_rowcol_to_cell(row-1, col+4)
                sum_formula = f'=SUM({cell_start}:{cell_end})'
                # total liter
                day_products = product_order.filtered(
                    lambda l: l.date_order >= datetime.combine(given_date.date(), time.min)  and l.date_order <= datetime.combine(given_date.date(), time.max)
                    )
                day_total_quantity = sum(map(lambda x: float(x.product_uom_qty), day_products))
                sheet.write_formula(row, col+4, sum_formula, number_style)
                col +=1
            
            cell_start = xl_rowcol_to_cell(4, col+4)  # E1
            cell_end = xl_rowcol_to_cell(row-1, col+3)
            sum_formula = f'=SUM({cell_start}:{cell_end})'
            sheet.write_formula(row, col+4, sum_formula, number_style)
            
            cell_start = xl_rowcol_to_cell(row, 3)  # E1
            cell_end = xl_rowcol_to_cell(row, col+4)
            sum_formula = f'{cell_start}+{cell_end}'
            sheet.write_formula(row, col+6, sum_formula, number_style)
            
            cell_start = xl_rowcol_to_cell(row, 2)  # E1
            cell_end = xl_rowcol_to_cell(row, col+6)
            sum_formula = f'={cell_start}+{cell_end}'
            sheet.write_formula(row, col+7, sum_formula, number_style)
            #     col += 1
                    # I1
            row +=2
        
        if jar_product:
            for product in jar_product:
                product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale'), '&', ('date_order', '>=', current_fiscal_date.date_from), ('date_order', '<=', current_fiscal_date.date_to)])
                old_product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale'), '&', ('date_order', '>=', previous_fiscal_date.date_from), ('date_order', '<=', previous_fiscal_date.date_to)])
                total_quantity = sum(map(lambda x: float(x.product_uom_qty), old_product_order))
                total_quantity_liter = sum(map(lambda x: float(x.product_uom_qty*20), old_product_order))
                fiscal_total_liter.append(total_quantity_liter)
                # last_week = product_order.filtered(
                #     lambda l: l.date_order >= start_date  and l.date_order <= end_date
                # )
                last_week = product_order.filtered(
                    lambda l: (
                    l.date_order.year == start_date.year and
                    l.date_order.month == start_date.month and
                    l.date_order < start_date
                ))
                last_week_total_quantity = sum(map(lambda x: float(x.product_uom_qty), last_week))
                last_week_total_liter = sum(map(lambda x: float(x.product_uom_qty*20), last_week))
                last_week_liter.append(last_week_total_liter)
                sheet.write(row, 0, product.name, text_style)
                sheet.write(row, 1, product.uom_id.name, text_style)
                sheet.write(row, 2, total_quantity, text_style)
                sheet.write(row, 3, last_week_total_quantity, text_style)
                col = 5
                for given_date in date_list:
                    day_products = product_order.filtered(
                    lambda l: l.date_order >= datetime.combine(given_date.date(), time.min)  and l.date_order <= datetime.combine(given_date.date(), time.max)
                    )
                    day_total_quantity = sum(map(lambda x: float(x.product_uom_qty), day_products))
                    sheet.write(row, col, day_total_quantity, text_style)
                    col += 1
                cell_start = xl_rowcol_to_cell(row, 5)  # E1
                cell_end = xl_rowcol_to_cell(row, col-1)
                sum_formula = f'=SUM({cell_start}:{cell_end})'
                sheet.write_formula(row, col, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 3)  # E1
                cell_end = xl_rowcol_to_cell(row, col)
                sum_formula = f'{cell_start}+{cell_end}'
                sheet.write_formula(row, col+2, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 2)  # E1
                cell_end = xl_rowcol_to_cell(row, col+2)
                sum_formula = f'={cell_start}+{cell_end}'
                sheet.write_formula(row, col+3, sum_formula, text_style)
                row += 1
         
            row +=1
        
        sheet.write(row,0,'Total',number_style)
        cell_start = xl_rowcol_to_cell(case_total_row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row-2, 2)
        sum_formula =  f'={cell_start}+{cell_end}'
        sheet.write_formula(row, 2, sum_formula, number_style)
        sheet.write(row, 1, '', number_style)
        cell_start = xl_rowcol_to_cell(case_total_row, 3)  # E1
        cell_end = xl_rowcol_to_cell(row-2, 3)
        sum_formula =  f'={cell_start}+{cell_end}'
        sheet.write_formula(row, 3, sum_formula, number_style)
        
        col = 1
        while len(date_list) >= col:
            cell_start = xl_rowcol_to_cell(case_total_row, col+4)
            cell_end = xl_rowcol_to_cell(row-2, col+4)
            sum_formula = f'={cell_start}+{cell_end}'
            sheet.write_formula(row, col+4, sum_formula, number_style)
            col +=1
        cell_start = xl_rowcol_to_cell(row, 5) 
        cell_end = xl_rowcol_to_cell(row, col+3)
        sum_formula = f'=SUM({cell_start}:{cell_end})'
        sheet.write_formula(row, col+4, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(row, 3) 
        cell_end = xl_rowcol_to_cell(row, col+4)
        sum_formula = f'{cell_start}+{cell_end}'
        sheet.write_formula(row, col+6, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row, col+6)
        sum_formula = f'={cell_start}+{cell_end}'
        sheet.write_formula(row, col+7, sum_formula, number_style)
        row += 1
        
        sheet.write(row,0,'Total (Liter)',number_style)
        sheet.write(row,1,'',number_style)
        cell_start = xl_rowcol_to_cell(case_total_row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row-2, 2)
        sum_formula =  f'={cell_start}+{cell_end}'
        sheet.write_formula(row, 2, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(case_total_row, 3)  # E1
        cell_end = xl_rowcol_to_cell(row-2, 3)
        sum_formula =  f'={cell_start}+{cell_end}'
        sheet.write(row, 2, str(sum(fiscal_total_liter)), number_style)
        sheet.write(row, 3, str(sum(last_week_liter)), number_style)
        
        col = 1
        # day product total
        while len(date_list) >= col:
            liter_product_order = request.env['sale.order.line'].search([('product_id', 'in', case_product.ids), ('state', '=', 'sale'), '&', ('date_order', '>=', datetime.combine(date_list[col-1].date(), time.min)), ('date_order', '<=', datetime.combine(date_list[col-1].date(), time.max))])
            day_total_quantity_liter = sum(
                            map(lambda x: float(x.product_uom_qty * (6 if '250ML' in x.product_id.name else 12)), liter_product_order)
                        )
            jar_liter_product_order = request.env['sale.order.line'].search([('product_id', 'in', jar_product.ids), ('state', '=', 'sale'), '&', ('date_order', '>=', datetime.combine(date_list[col-1].date(), time.min)), ('date_order', '<=', datetime.combine(date_list[col-1].date(), time.max))])
            jar_total_quantity_liter = sum(
                            map(lambda x: float(x.product_uom_qty * 20), jar_liter_product_order)
                        )
            # cell_start = xl_rowcol_to_cell(case_total_row, col+4)
            # cell_end = xl_rowcol_to_cell(row-2, col+4)
            # sum_formula = f'={cell_start}+{cell_end}'
            # sheet.write_formula(row, col+4, sum_formula, text_style)
            sheet.write(row, col+4, day_total_quantity_liter+jar_total_quantity_liter, number_style)
            col +=1
        # this week liter total
        cell_start = xl_rowcol_to_cell(row, 5) 
        cell_end = xl_rowcol_to_cell(row, col+3)
        sum_formula = f'=SUM({cell_start}:{cell_end})'
        sheet.write_formula(row, col+4, sum_formula, number_style)
        
        # current month total
        cell_start = xl_rowcol_to_cell(row, 3) 
        cell_end = xl_rowcol_to_cell(row, col+4)
        sum_formula = f'{cell_start}+{cell_end}'
        sheet.write_formula(row, col+6, sum_formula, number_style)
        
        # total all sales
        cell_start = xl_rowcol_to_cell(row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row, col+6)
        sum_formula = f'={cell_start}+{cell_end}'
        sheet.write_formula(row, col+7, sum_formula, number_style)
        liter_row = row
        row += 2
        
        sheet.write(row,0,'Amount',border_style)
        row+=1
        amount_row = row
        if case_product:
            for product in case_product:
                product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), 
                                                                       ('state', '=', 'sale'), 
                                                                       '&', ('date_order', '>=', current_fiscal_date.date_from), 
                                                                       ('date_order', '<=', current_fiscal_date.date_to)])
                old_product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale'), '&', ('date_order', '>=', previous_fiscal_date.date_from), ('date_order', '<=', previous_fiscal_date.date_to)])
                # total_quantity = sum(map(lambda x: float(x.product_uom_qty), old_product_order))
                total_amount = sum(map(lambda x: float(x.price_subtotal), old_product_order))
                last_week = product_order.filtered(
                    lambda l: (
                    l.date_order.year == start_date.year and
                    l.date_order.month == start_date.month and
                    l.date_order < start_date
                ))
                last_week_total_amount = sum(map(lambda x: float(x.price_subtotal), last_week))
                sheet.write(row, 0, product.name, text_style)
                sheet.write(row, 1, product.currency_id.name, text_style)
                sheet.write(row, 2, total_amount, text_style)
                sheet.write(row, 3, last_week_total_amount, text_style)
                col = 5
                for given_date in date_list:
                    day_products = product_order.filtered(
                    lambda l: l.date_order >= datetime.combine(given_date.date(), time.min)  and l.date_order <= datetime.combine(given_date.date(), time.max)
                    )
                    day_total_amount = sum(map(lambda x: float(x.price_subtotal), day_products))
                    sheet.write(row, col, day_total_amount, text_style)
                    col += 1
                cell_start = xl_rowcol_to_cell(row, 5)  # E1
                cell_end = xl_rowcol_to_cell(row, col-1)
                sum_formula = f'=SUM({cell_start}:{cell_end})'
                sheet.write_formula(row, col, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 3)  # E1
                cell_end = xl_rowcol_to_cell(row, col)
                sum_formula = f'{cell_start}+{cell_end}'
                sheet.write_formula(row, col+2, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 2)  # E1
                cell_end = xl_rowcol_to_cell(row, col+2)
                sum_formula = f'={cell_start}+{cell_end}'
                sheet.write_formula(row, col+3, sum_formula, text_style)
                row += 1
            case_total_row = row
            sheet.write(row, 0, 'Sub Total (Case)', number_style)
            sheet.write(row, 1, '', number_style)
            amount_sum_start = xl_rowcol_to_cell(4, 2)
            amount_sum_end = xl_rowcol_to_cell(row-1, 2)
            amount_formula = f'=SUM({amount_sum_start}:{amount_sum_end})'
            sheet.write_formula(row, 2, amount_formula, number_style)
            fiscal_amount_sum_start = xl_rowcol_to_cell(4, 3)
            fiscal_amount_sum_end = xl_rowcol_to_cell(row-1, 3)
            fiscal_amount_formula = f'=SUM({fiscal_amount_sum_start}:{fiscal_amount_sum_end})'
            sheet.write_formula(row, 3, fiscal_amount_formula, number_style)
            col = 1
            while len(date_list) >= col:
                cell_start = xl_rowcol_to_cell(amount_row, col+4)
                cell_end = xl_rowcol_to_cell(row-1, col+4)
                sum_formula = f'=SUM({cell_start}:{cell_end})'
                sheet.write_formula(row, col+4, sum_formula, number_style)
                col +=1
            
            cell_start = xl_rowcol_to_cell(amount_row, col+4)  # E1
            cell_end = xl_rowcol_to_cell(row-1, col+3)
            sum_formula = f'=SUM({cell_start}:{cell_end})'
            sheet.write_formula(row, col+4, sum_formula, number_style)
            
            cell_start = xl_rowcol_to_cell(row, 3)  # E1
            cell_end = xl_rowcol_to_cell(row, col+4)
            sum_formula = f'{cell_start}+{cell_end}'
            sheet.write_formula(row, col+6, sum_formula, number_style)
            
            cell_start = xl_rowcol_to_cell(row, 2)  # E1
            cell_end = xl_rowcol_to_cell(row, col+6)
            sum_formula = f'={cell_start}+{cell_end}'
            sheet.write_formula(row, col+7, sum_formula, number_style)
            #     col += 1
                    # I1
            row +=2
        
        if jar_product:
            for product in jar_product:
                product_order = request.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale'), '&', ('date_order', '>=', current_fiscal_date.date_from), ('date_order', '<=', current_fiscal_date.date_to)])
                total_amount = sum(map(lambda x: float(x.price_subtotal), product_order))
                last_week = product_order.filtered(
                    lambda l: l.date_order >= start_date  and l.date_order <= end_date
                )
                last_week_total_amount = sum(map(lambda x: float(x.price_subtotal), last_week))
                sheet.write(row, 0, product.name, text_style)
                sheet.write(row, 1, product.currency_id.name, text_style)
                sheet.write(row, 2, total_amount, text_style)
                sheet.write(row, 3, last_week_total_amount, text_style)
                col = 5
                for given_date in date_list:
                    day_products = product_order.filtered(
                    lambda l: l.date_order >= datetime.combine(given_date.date(), time.min)  and l.date_order <= datetime.combine(given_date.date(), time.max)
                    )
                    day_total_amount = sum(map(lambda x: float(x.price_subtotal), day_products))
                    sheet.write(row, col, day_total_amount, text_style)
                    col += 1
                cell_start = xl_rowcol_to_cell(row, 5)  # E1
                cell_end = xl_rowcol_to_cell(row, col-1)
                sum_formula = f'=SUM({cell_start}:{cell_end})'
                sheet.write_formula(row, col, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 3)  # E1
                cell_end = xl_rowcol_to_cell(row, col)
                sum_formula = f'{cell_start}+{cell_end}'
                sheet.write_formula(row, col+2, sum_formula, text_style)
                
                cell_start = xl_rowcol_to_cell(row, 2)  # E1
                cell_end = xl_rowcol_to_cell(row, col+2)
                sum_formula = f'={cell_start}+{cell_end}'
                sheet.write_formula(row, col+3, sum_formula, text_style)
                row += 1
         
            row +=1
        
        sheet.write(row,0,'Total',number_style)
        cell_start = xl_rowcol_to_cell(case_total_row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row-2, 2)
        sum_formula =  f'={cell_start}+{cell_end}'
        sheet.write_formula(row, 2, sum_formula, number_style)
        sheet.write(row, 1, '', number_style)
        cell_start = xl_rowcol_to_cell(case_total_row, 3)  # E1
        cell_end = xl_rowcol_to_cell(row-2, 3)
        sum_formula =  f'={cell_start}+{cell_end}'
        sheet.write_formula(row, 3, sum_formula, number_style)
        
        col = 1
        while len(date_list) >= col:
            cell_start = xl_rowcol_to_cell(case_total_row, col+4)
            cell_end = xl_rowcol_to_cell(row-2, col+4)
            sum_formula = f'={cell_start}+{cell_end}'
            sheet.write_formula(row, col+4, sum_formula, number_style)
            col +=1
        cell_start = xl_rowcol_to_cell(row, 5) 
        cell_end = xl_rowcol_to_cell(row, col+3)
        sum_formula = f'=SUM({cell_start}:{cell_end})'
        sheet.write_formula(row, col+4, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(case_total_row, col+2) 
        cell_end = xl_rowcol_to_cell(row-2, col+2)
        sum_formula = f'{cell_start}+{cell_end}'
        sheet.write_formula(row, col+6, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row, col+6)
        sum_formula = f'={cell_start}+{cell_end}'
        sheet.write_formula(row, col+7, sum_formula, number_style)
        row += 1
        
        sheet.write(row,0,'Rate/Ltr Combined',number_style)
        cell_start = xl_rowcol_to_cell(liter_row, 2)  # E1
        cell_end = xl_rowcol_to_cell(row-1, 2)
        sum_formula =  f'={cell_start}/{cell_end}'
        sheet.write_formula(row, 2, sum_formula, number_style)
        sheet.write(row, 1, '', number_style)
        cell_start = xl_rowcol_to_cell(liter_row, 3)  # E1
        cell_end = xl_rowcol_to_cell(row-1, 3)
        sum_formula =  f'={cell_start}/{cell_end}'
        sheet.write_formula(row, 3, sum_formula, number_style)
        
        col = 1
        while len(date_list) >= col:
            cell_start = xl_rowcol_to_cell(liter_row, col+4)
            cell_end = xl_rowcol_to_cell(row-1, col+4)
            sum_formula = f'={cell_start}/{cell_end}'
            sheet.write_formula(row, col+4, sum_formula, number_style)
            col +=1
        cell_start = xl_rowcol_to_cell(liter_row, col+4) 
        cell_end = xl_rowcol_to_cell(row-1, col+4)
        sum_formula = f'{cell_start}/{cell_end}'
        sheet.write_formula(row, col+4, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(liter_row, col+6) 
        cell_end = xl_rowcol_to_cell(row-1, col+6)
        sum_formula = f'{cell_start}/{cell_end}'
        sheet.write_formula(row, col+6, sum_formula, number_style)
        
        cell_start = xl_rowcol_to_cell(liter_row, col+7)
        cell_end = xl_rowcol_to_cell(row-1, col+7)
        sum_formula = f'={cell_start}/{cell_end}'
        sheet.write_formula(row, col+7, sum_formula, number_style)
        row += 2
        
        start_cell = xl_rowcol_to_cell(0,0) # Excel row col is 0 indexed, but range is 1 indexed
        end_cell = xl_rowcol_to_cell(row, col+7)
        range_str = f"{start_cell}:{end_cell}"
        
        sheet.conditional_format(range_str, {
            'type': 'no_blanks', #applies to non blank cells
            'format': dark_border_format,
        })
        sheet.conditional_format(range_str, {
            'type': 'blanks', #applies to blank cells
            'format': dark_border_format,
        })

        # return the excel file as a response, so the browser can download it
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
