from pydantic import ValidationError
from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from odoo.http import request
from odoo import http, Command, SUPERUSER_ID
from .schema.order import GetPayment, OrderDetails
from datetime import date, datetime
import json
import base64
import logging

_logger = logging.getLogger(__name__)

class PaymentController(http.Controller):

    # def calculate_outstanding(self,move):
    #     if move.invoice_has_outstanding:
    #         if move.state != 'posted' \
    #                 or move.payment_state not in ('not_paid', 'partial') \
    #                 or not move.is_invoice(include_receipts=True):
    #             pass

    #         else:

    #             pay_term_lines = move.line_ids\
    #                 .filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

    #             domain = [
    #                 ('account_id', 'in', pay_term_lines.account_id.ids),
    #                 ('parent_state', '=', 'posted'),
    #                 ('partner_id', '=', move.commercial_partner_id.id),
    #                 ('reconciled', '=', False),
    #                 '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
    #             ]

    #             payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

    #             if move.is_inbound():
    #                 domain.append(('balance', '<', 0.0))
    #                 payments_widget_vals['title'] = _('Outstanding credits')

    #                 for line in self.env['account.move.line'].search(domain):

    #                 if line.currency_id == move.currency_id:
    #                     # Same foreign currency.
    #                     amount = abs(line.amount_residual_currency)
    #                 else:
    #                     # Different foreign currencies.
    #                     amount = line.company_currency_id._convert(
    #                         abs(line.amount_residual),
    #                         move.currency_id,
    #                         move.company_id,
    #                         line.date,
    #                     )

    #                 if move.currency_id.is_zero(amount):
    #                     continue

    #                 self.js_assign_outstanding_line(line.id)

    @http.route('/api/v1/collect-payments', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def sale_payment(self, **kwargs):
        try:
            payment = GetPayment(**kwargs)

            amount_paid = 0
            total_sent = 0
            amount_left_send = 0
            payments = []
            for sent_order in payment.orders:
                order = request.env['sale.order'].sudo().search([
                    ('id', '=', sent_order.order_id)
                ], limit=1) 

                if not order:
                    raise Exception("Order Not Found")
                
                _logger.info("_____________________________________")
                _logger.info(SUPERUSER_ID)
                _logger.info(sent_order)
                _logger.info("_____________________________________")
                invoices = request.env['account.move'].with_user(SUPERUSER_ID).sudo().search([('id', 'in', order.invoice_ids.ids), ('state', '=', 'posted')], order='invoice_date asc')
                _logger.info(invoices)
                if not invoices:
                    raise Exception("No posted invoices found!")

                for method in payment.payments:
                    if method.paid == method.amount:
                        continue
                    payment_date = date.today()

                    amount_sent = method.amount
                    if method.paid > 0:
                        amount_sent = amount_left
                
                    journal_code_mapping = {
                        "cheque": "CQ", 
                        "fonepay": "FP",
                        "cash":  "CSH1"
                    }
                                    
                    journal_code = journal_code_mapping.get(method.payment_method, "CSH1")

                    journal  = request.env['account.journal'].with_user(SUPERUSER_ID).search([
                        ("code", '=', journal_code)
                    ],limit=1)
                    if not journal:
                        raise Exception("Journal is not Set Properly. Please Contact Admin.")
                    
                    if journal_code == 'CQ':
                        payment_date = datetime.strptime(method.date, '%Y-%m-%d').date() or date.today()
                    
                    for invoice in invoices:
                        amount_paid = 0
                        payment_amount = 0
                        if amount_sent > 0:
                            amount_to_pay = invoice.amount_residual
                            done_payments = request.env['account.payment'].with_user(SUPERUSER_ID).sudo().search([('id', 'in', invoice.matched_payment_ids.ids)])
                            if done_payments:
                                amount_paid += sum(map(lambda x: x.amount, done_payments))
                                amount_to_pay = invoice.amount_residual - amount_paid

                            if amount_to_pay > 0:
                                if amount_sent >= amount_to_pay:
                                    payment_amount = amount_to_pay
                                    amount_sent -= amount_to_pay
                                else:
                                    payment_amount = amount_sent
                                    amount_sent = 0

                                payment_register = request.env['account.payment.register'].with_user(SUPERUSER_ID).with_context(active_model='account.move', active_ids=invoice.id).create({
                                    "journal_id": journal.id,
                                    "amount": payment_amount,
                                    "payment_date": payment_date or date.today(),
                                    "group_payment": True,
                                    "payment_type": 'inbound'
                                })

                                payment_created = payment_register.with_user(SUPERUSER_ID).action_create_payments()

                                payments.append(payment_created['res_id'])

                            method.paid = payment_amount
                            amount_left = amount_sent
                            amount_left_send += payment_amount

            for method in payment.payments:
                total_sent += method.amount

            if total_sent > amount_left_send:
                payment_outstanding = request.env['account.payment'].with_user(SUPERUSER_ID).sudo().create({
                    "payment_type": 'inbound',
                    "partner_id": order.partner_id.id,
                    "amount": total_sent - amount_left_send,
                    "date": payment_date or date.today(),
                    'journal_id': journal.id,
                    "memo": method.remarks
                }) 
                payment_outstanding.with_user(SUPERUSER_ID).action_post()

            customer = request.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)])
            customer.is_payment_taken_today = True

            return response(
                status=200,
                message="Payments Created Successfully!",
                data = {
                    'payment': payments
                }

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

    @http.route('/api/v1/download-payment_receipt', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    # @check_role([UserRole.SALE_AGENT.value])
    def download_payment_receipt(self, **kwargs):
        try:
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            user_id = request.env.user.id
            payment_ids = kwargs['payment_ids']
            
            payments = request.env['account.payment'].sudo().search([('id', 'in', payment_ids)])
            if not payments:
                raise ValueError("Payment not found!!")

            report_action = request.env['ir.actions.report']._get_report_from_name('custom_payment_ledger.thermal_common_master_template_payment')
            pdf_content, _ = report_action.sudo()._render_qweb_pdf(report_action, res_ids=payments.ids)
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename=' + "payment_receipt.pdf;")
            ]
            name = "Payment Receipt.pdf"

            attachment = request.env['ir.attachment'].sudo().create({
                'name': "Payment Receipt",
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
                    "message": 'Payment Receipt generated successfully!!'
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