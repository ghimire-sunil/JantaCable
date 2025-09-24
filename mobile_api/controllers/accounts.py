from odoo import http
from odoo.http import request, Response
from pydantic import ValidationError
from odoo.exceptions import UserError
from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from .schema.account import Account
from datetime import date
import json
import base64

class AccountsController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/customer-due', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def salesperson_customer_due(self, **kwargs):
        try:
            if 'customer_id' not in kwargs:
                raise UserError("Please choose a customer!")
            
            customer_id = kwargs['customer_id']
            
            data = []
            invoice_list = request.env['account.move'].sudo().search([('partner_id','=',customer_id), ("move_type", "=", "out_invoice")])
            
            for invoice in invoice_list:
                invoice_details = {
                    'invoice_id': invoice.id,
                    'invoice_name': invoice.name,
                    'date': invoice.invoice_date,
                    'tax_excluded': invoice.amount_untaxed_in_currency_signed,
                    'total': invoice.amount_total_in_currency_signed,
                    'payment_status': invoice.status_in_payment,
                    'amount_due': invoice.amount_residual,
                    'invoice_date_due': invoice.invoice_date_due
                }
                data.append(invoice_details)
            
            return response(
                status=200,
                message="Customer Invoices Fetched Successfully",
                data=data
            )
                        
        except UserError as error:    
            return response(
                status=400,
                message=error,
                data=None
            )        
                 
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        
        
    @http.route('/api/v1/customer-partner-ledger', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def salesperson_customer_partner_ledger(self, **kwargs):
        try:
            if 'customer_id' not in kwargs:
                raise UserError("Please choose a customer!")
            
            customer_id = kwargs['customer_id']

            data = []
            total_debit = 0
            total_credit = 0
            total_balance = 0
            move_line = request.env['account.move.line'].sudo().search([('partner_id','=',customer_id)])

            # first_line = request.env['account.move.line'].sudo().search([('partner_id','=',customer_id)], order='date, id desc', limit=1)
            # move_id = first_line.move_id
            # old_balance = first_line.balance
            old_balance = 0
        
            for line in move_line:
                total_debit += line.debit
                total_credit += line.credit

                # if line.move_id == move_id and line.id != first_line.id:
                balance = old_balance + line.debit - line.credit
                old_balance = round(balance,2)
                # else:
                #     balance = line.debit - line.credit
                #     old_balance = balance
                #     print(balance)

                line_details = {
                    'date': line.date,
                    'journal_entry': line.move_name,
                    'label': line.name,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': round(balance,2)
                }

                data.append(line_details)

            data.append({
                'total': {
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'total_balance': total_debit - total_credit      
                }  
            })
            
            return response(
                status=200,
                message="Partner Ledger Fetched Successfully",
                data=data
            )
                
        except UserError as error:    
            return response(
                status=400,
                message=error,
                data=None
            )
                 
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )

    @http.route('/api/v1/download-partner-ledger', type='http', methods=['GET', 'POST'], auth='public', csrf=False)
    @required_login
    @make_response
    def download_partner_ledger(self, **kwargs):
        try:
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            user = request.env.user
            account = Account(**kwargs)

            if request.env.user.role in ['sale_agent', 'sale_person']:
                customer_id = account.customer_id
                print(customer_id)
                if not customer_id:
                    raise UserError("Please select a customer!")

            else:
                customer_id = user.partner_id.id

            customer = request.env['res.partner'].sudo().search([('id', '=', customer_id)])
            total_debit = 0.0
            total_credit = 0.0
            old_balance = 0
            data = {
                'customer_name': customer.name,
                'lines': [],
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': 0
            }

            move_line = request.env['account.move.line'].sudo().search([('partner_id','=',customer_id)])

            for line in move_line:
                total_debit += line.debit
                total_credit += line.credit
                journal_date = str(line.date)

                balance = old_balance + line.debit - line.credit
                old_balance = round(balance,2)

                line_details = {
                    'journal_date': journal_date,
                    'journal_entry': line.move_name,
                    'label': line.name,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': round(balance,2)
                }
                data['lines'].append(line_details)

            data['total_debit'] = total_debit
            data['total_debit'] = total_credit
            data['total_debit'] = total_debit - total_credit           

            report_action = http.request.env['ir.actions.report'].sudo()
            pdf_content, __ = report_action._render_qweb_pdf(
                'mobile_api.action_customer_partner_ledger',
                move_line.ids,
                data={'data': data}
            )
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename=' + "customer_partner_ledger.pdf;")
            ]

            name = customer.name + " - Partner Ledger.pdf"

            attachment = request.env['ir.attachment'].sudo().create({
                'name': customer.name + "- Partner Ledger",
                'type': 'binary',
                'raw': pdf_content,
                'store_fname': name,
                'mimetype': 'application/pdf'
            })

            download_url = f"{system_url}/web/content/{attachment.id}?download=true"

            return {
                'result': {
                    "status": 200,
                    "data": base64.b64encode(pdf_content).decode('utf-8'),
                    "url": download_url,
                    "message": 'Customer Ledger PDF generated successfully!!'
                },
                "headers": pdfhttpheaders
            }
                 
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        
    @http.route('/api/v1/download-customer-due', type='http', methods=['GET', 'POST'], auth='public', csrf=False)
    @required_login
    @make_response
    def download_customer_due(self, **kwargs):
        try:
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            user = request.env.user
            account = Account(**kwargs)

            if request.env.user.role in ['sale_agent', 'sale_person']:
                customer_id = account.customer_id
                print(customer_id)
                if not customer_id:
                    raise UserError("Please select a customer!")

            else:
                customer_id = user.partner_id.id

            customer = request.env['res.partner'].sudo().search([('id', '=', customer_id)])
            data = {
                'customer_name': customer.name,
                'lines': []
            }

            invoice_list = request.env['account.move'].sudo().search([('partner_id','=',customer_id), ("move_type", "=", "out_invoice")])

            for invoice in invoice_list:
                invoice_details = {
                    'invoice_id': invoice.id,
                    'invoice_name': invoice.name,
                    'date': invoice.invoice_date,
                    'tax_excluded': invoice.amount_untaxed_in_currency_signed,
                    'total': invoice.amount_total_in_currency_signed,
                    'payment_status': invoice.status_in_payment,
                    'amount_due': invoice.amount_residual,
                    'invoice_date_due': invoice.invoice_date_due
                }
                data['lines'].append(invoice_details)

            report_action = http.request.env['ir.actions.report'].sudo()
            pdf_content, __ = report_action._render_qweb_pdf(
                'mobile_api.action_customer_due',
                invoice_list.ids,
                data={'data': data}
            )
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename=' + "customer_partner_ledger.pdf;")
            ]

            name = customer.name + "- Customer Due.pdf"

            attachment = request.env['ir.attachment'].sudo().create({
                'name': customer.name + " - Customer Due",
                'type': 'binary',
                'raw': pdf_content,
                'store_fname': name,
                'mimetype': 'application/pdf'
            })

            download_url = f"{system_url}/web/content/{attachment.id}?download=true"

            return {
                'result': {
                    "status": 200,
                    "data": base64.b64encode(pdf_content).decode('utf-8'),
                    "url": download_url,
                    "message": 'PDF generated successfully!!'
                },
                "headers": pdfhttpheaders
            }
                 
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )

    # def add_data(self, line, lines):
    #     journal_date = str(line.date)
    #     line_details = {
    #         'journal_date': journal_date,
    #         'journal_entry': line.move_name,
    #         'label': line.name,
    #         'debit': line.debit,
    #         'credit': line.credit,
    #     }
    #     lines.append(line_details)

    # def create_report(self, data, move_line, partner, system_url):
        
    #     report_action = http.request.env['ir.actions.report'].sudo()
    #     pdf_content, __ = report_action._render_qweb_pdf(
    #         'api.action_sale_partner_ledger',
    #         move_line.ids,
    #         data= {
    #             'name': request.env.user.name,
    #             'data': data
    #         }
    #     )
        
    #     pdfhttpheaders = [
    #         ('Content-Type', 'application/pdf'),
    #         ('Content-Disposition', 'attachment; filename=' + "customer_partner_ledger.pdf;")
    #     ]
    #     name = partner.name + " - Partner Ledger.pdf"
    #     attachment = request.env['ir.attachment'].sudo().create({
    #         'name': partner.name + "- Partner Ledger",
    #         'type': 'binary',
    #         'raw': pdf_content,
    #         'store_fname': name,
    #         'mimetype': 'application/pdf'
    #     })
    #     download_url = f"{system_url}/web/content/{attachment.id}?download=true"

    #     return {
    #         'result': {
    #             "status": 200,
    #             "data": base64.b64encode(pdf_content).decode('utf-8'),
    #             "url": download_url,
    #             "message": 'Customer Ledger PDF generated successfully!!'
    #         },
    #         "headers": pdfhttpheaders
    #     }

    # @http.route('/api/v1/partner-ledger-sale', type='http', methods=['GET'], auth='public', csrf=False)
    # @required_login
    # @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    # @make_response
    # def partner_ledger_sale(self, **kwargs):
    #     try:
    #         system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #         user = request.env.user.id
    #         data = []

    #         if request.env.user.role == 'sale_agent':
    #             routes = request.env['user.route.schedule'].sudo().search([('user_id', '=', user), ('date', '=', date.today())])
    #             if not routes:
    #                 raise Exception("Route Not Set.")

    #             for route in routes:
    #                 for partner_route in route.route_id:
    #                     for partner in partner_route.partners_ids:
    #                         lines = []
    #                         customer = {
    #                             'customer_name': partner.name,
    #                             'lines': lines
    #                         }

    #                         move_line = request.env['account.move.line'].sudo().search([('partner_id','=',partner.id)])
                            
    #                         for line in move_line:
    #                             self.add_data(line, lines)

    #                         data.append(customer)

    #                     move_lines = request.env['account.move.line'].sudo().search([('partner_id','in',partner_route.partners_ids.ids)])


    #         elif request.env.user.role == 'sale_person':
    #             partners = request.env['res.partner'].sudo().search([('user_id', '=', user)])
    #             for partner in partners:

    #                 lines = []
    #                 customer = {
    #                     'customer_name': partner.name,
    #                     'lines': lines
    #                 }
    #                 move_line = request.env['account.move.line'].sudo().search([('partner_id','=',partner.id)])
                    
    #                 for line in move_line:
    #                     self.add_data(line, lines)
    #                 data.append(customer)

    #             move_lines = request.env['account.move.line'].sudo().search([('partner_id','in',partners.ids)])

    #         return self.create_report(data, move_lines, partner, system_url)                
                 
    #     except ValidationError as error:    
    #         return response(
    #             status=400,
    #             message="Data Validation Error",
    #             data=formate_error(error.errors())
    #         )
        
    #     except Exception as e:
    #         return response(
    #             status=400,
    #             message=e.args[0],
    #             data=None
    #         )


    # @http.route('/api/v1/customer-due-sale', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    # @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    # def customer_due_sale(self, **kwargs):
    #     try:
    #         if 'customer_id' not in kwargs:
    #             raise UserError("Please choose a customer!")
            
    #         customer_id = kwargs['customer_id']
            
    #         data = []
    #         invoice_list = request.env['account.move'].sudo().search([('partner_id','=',customer_id), ("move_type", "=", "out_invoice")])
            
    #         for invoice in invoice_list:
    #             invoice_details = {
    #                 'invoice_id': invoice.id,
    #                 'invoice_name': invoice.name,
    #                 'date': invoice.invoice_date,
    #                 'tax_excluded': invoice.amount_untaxed_in_currency_signed,
    #                 'total': invoice.amount_total_in_currency_signed,
    #                 'payment_status': invoice.status_in_payment,
    #                 'amount_due': invoice.amount_residual
    #             }
    #             data.append(invoice_details)
            
    #         return response(
    #             status=200,
    #             message="Customer Invoices Fetched Successfully",
    #             data=data
    #         )
                        
    #     except UserError as error:    
    #         return response(
    #             status=400,
    #             message=error,
    #             data=None
    #         )        
                 
    #     except ValidationError as error:    
    #         return response(
    #             status=400,
    #             message="Data Validation Error",
    #             data=formate_error(error.errors())
    #         )
        
    #     except Exception as e:
    #         return response(
    #             status=400,
    #             message=e.args[0],
    #             data=None
    #         )
        