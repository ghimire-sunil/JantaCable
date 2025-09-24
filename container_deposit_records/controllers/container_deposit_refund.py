from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from datetime import timedelta, datetime
from odoo.exceptions import UserError


class SaleExcelReportController(http.Controller):
    @http.route([
        '/container_deposit/excel_report/<model("container.deposit.refund.wizard"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_deposit_refund_report(self, wizard=None, **args):
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
                    content_disposition(str(wizard.from_date) + ' - ' + str(wizard.to_date) + 'Container Deposit and Refund.xlsx'))
            ]
        )


        # create workbook object from xlsxwriter library
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # create some style to set up the font type, the font size, the border, and the aligment
        title_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 20, 'font_color': '#c9211e', 'bold': True, 'align': 'center'})
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        initial_style = workbook.add_format(
            {'font_name': 'Times',  'font_color': 'red', 'italic': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        right_style = workbook.add_format(
            {'font_name': 'Times', 'italic': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        blue_style = workbook.add_format(
            {'font_name': 'Times', 'font_size': 12, 'font_color': 'blue', 'underline':True, 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})

        # create worksheet/tab per salesperson
        sheet = workbook.add_worksheet("Sales Book")
        # set the orientation to landscape
        sheet.set_landscape()
        # set up the paper size, 9 means A4
        sheet.set_paper(9)
        # set up the margin in inch
        sheet.set_margins(0.5, 0.5, 0.5, 0.5)

        # set up the column width
        sheet.set_column('A:A', 5)
        sheet.set_column('B:E', 15)


        # the report title
        # merge the A1 to E1 cell and apply the style font size : 14, font weight : bold
        # company = wizard.company_id
        # sheet.merge_range('A1:J1', 'Purchase Additional Register', title_style)
        sheet.write(0, 0, 'Accounting Period', initial_style)
        sheet.write(
            1, 0, f'{wizard.from_date.strftime("%d/%m/%Y")} - {wizard.to_date.strftime("%d/%m/%Y")}', right_style)
        sheet.write(2, 0, 'Dt/Time: ' + f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', right_style)

        # sheet.write(4, 0, company.name, title_style)

        sheet.write(6, 0, 'Container Deposit and Refund', blue_style)
        sheet.write(7, 0, 'Report Date 'f'{wizard.from_date.strftime("%d/%m/%Y")} - {wizard.to_date.strftime("%d/%m/%Y")}', blue_style)

        sheet.write(9, 0, 'Name', header_style)
        sheet.write(9, 1, 'Journal', header_style)
        sheet.write(9, 2, "Account", header_style)
        sheet.write(9, 3, "Invoice Date", header_style)
        sheet.write(9, 4, 'Invoice Dute Date', header_style)
        sheet.write(9, 5, 'Matching', header_style)
        sheet.write(9, 6, 'Debit', header_style)
        sheet.write(9, 7, 'Credit', header_style)
        sheet.write(9, 8, 'Amount Currency', header_style)
        sheet.write(9, 9, 'Balance', header_style)

        
        
        move_lines = request.env['account.move.line'].sudo().search([('partner_id', '=', wizard.partner_id.id), ("date", "<", wizard.from_date),"|", "&", ("account_id.account_type", "=", "liability_payable"), ("account_id.non_trade", "=", False), "&", ("account_id.account_type", "=", "asset_receivable"), ("account_id.non_trade", "=", False)])
        
        initial_balance = sum(map(lambda x: float(x.balance), move_lines))
        sheet.write(10,0,"Initial Balance", text_style)
        for col in range(1,6):
            sheet.write(10,col,"", text_style)
        sheet.write(10,7,initial_balance,text_style)
        sheet.write(10,8,initial_balance,text_style)
        sheet.write(10,9,initial_balance,text_style)

        container_deposits = request.env['container.deposit.records'].sudo().search([('partner_id','=',wizard.partner_id.id)])
        
        row = 11
        total_debit = 0
        total_credit = 0
        old_balance = 0

        for deposit in container_deposits:
            for entry in deposit.entry_ids:
                for line in entry.line_ids:
                    if (line.account_id.account_type == "liability_payable" and line.account_id.non_trade == False) or (line.account_id.account_type == "asset_receivable" and line.account_id.non_trade == False):
                        total_debit += line.debit
                        total_credit += line.credit

                        balance = old_balance + line.debit - line.credit
                        old_balance = round(balance,2)

                        sheet.write(row, 0, entry.name, text_style)
                        sheet.write(row, 1, entry.journal_id.name, text_style)
                        sheet.write(row, 2, line.account_id.name, text_style)
                        sheet.write(row, 3, entry.date, text_style)
                        sheet.write(row, 4, entry.invoice_date_due, text_style)
                        sheet.write(row, 5, line.matching_number, text_style)
                        sheet.write(row, 6, line.debit, text_style)
                        sheet.write(row, 7, line.credit, text_style)
                        sheet.write(row, 8, line.amount_currency, text_style)
                        sheet.write(row, 9, balance, text_style)

                        row += 1

            for payment in deposit.payments:
                for line in payment.move_id.line_ids:
                    if (line.account_id.account_type == "liability_payable" and line.account_id.non_trade == False) or (line.account_id.account_type == "asset_receivable" and line.account_id.non_trade == False):
                        total_debit += line.debit
                        total_credit += line.credit

                        balance = old_balance + line.debit - line.credit
                        old_balance = round(balance,2)

                        sheet.write(row, 0, payment.move_id.name, text_style)
                        sheet.write(row, 1, payment.move_id.journal_id.name, text_style)
                        sheet.write(row, 2, line.account_id.name, text_style)
                        sheet.write(row, 3, payment.move_id.date, text_style)
                        sheet.write(row, 4, payment.move_id.invoice_date_due, text_style)
                        sheet.write(row, 5, line.matching_number, text_style)
                        sheet.write(row, 6, line.debit, text_style)
                        sheet.write(row, 7, line.credit, text_style)
                        sheet.write(row, 8, line.amount_currency, text_style)
                        sheet.write(row, 9, balance, text_style)

                        row += 1

        # for order in orders:
        #     vat_id_line = request.env['account.move.line'].search([('move_id', '=', order.id),('product_id', '=', vat_id.id)])
        #     import_cc_line = request.env['account.move.line'].search([('move_id', '=', order.id),('product_id', '=', import_cc_id.id)])
        #     import_duty_line = request.env['account.move.line'].search([('move_id', '=', order.id),('product_id', '=', import_duty_id.id)])
        #     # the report content
        #     sheet.write(row, 0, order.invoice_date.strftime("%d/%m/%Y"), text_style)
        #     sheet.write(row, 1, order.name, text_style)
        #     sheet.write(row, 2, order.ref, text_style)
        #     sheet.write(row, 3, vat_id_line.price_subtotal if vat_id_line else None, number_style)
        #     sheet.write(row, 4, import_cc_line.price_subtotal if import_cc_line else None, number_style)
        #     sheet.write(row, 5, import_duty_line.price_subtotal if import_duty_line else None, number_style)
        #     print(import_duty_line)
        #     print(import_duty_line.price_subtotal)
        #     sheet.write(row, 6, int(vat_id_line.price_subtotal+import_cc_line.price_subtotal+import_duty_line.price_subtotal), number_style)

        #     row += 1

        # create a formula to sum the total salesresponse
        # sheet.merge_range('A' + str(row+1) + ':D' + str(row+1), 'Total', text_style)
        # sheet.write(row, 2, "Grand Total", header_style)
        # sheet.write_formula(
        #     row, 3, '=SUM(D11:D' + str(row) + ')', number_style)
        # sheet.write_formula(
        #     row, 4, '=SUM(E11:E' + str(row) + ')', number_style)
        # sheet.write_formula(
        #     row, 5, '=SUM(F11:F' + str(row) + ')', number_style)



        # return the excel file as a response, so the browser can download it
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
