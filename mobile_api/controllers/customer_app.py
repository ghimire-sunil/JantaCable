import uuid
from odoo import http
from odoo.http import request, Response

from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from .schema.customer import Contact
from pydantic import ValidationError
from datetime import date, datetime, timedelta
import calendar
import base64
import json

class CustomerAppController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/customer/dashboard', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @check_role([UserRole.CUSTOMER.value])
    @required_login
    def customer_dashboard(self, **kwargs):
        try:
            user_id = request.env.user.id
            # user_id = kwargs['user_id']
            user = request.env['res.users'].sudo().search([('id','=',user_id)])

            if user.partner_id:
                partner_id = user.partner_id.id
                end_date = calendar.monthrange(date.today().year, date.today().month)[1]
                month_start = str(date.today().year) + "-" + str(date.today().month) + "-01"
                month_end = str(date.today().year) + "-" + str(date.today().month) + "-" + str(end_date)

                orders = []
                monthly_pending_amount = 0
                monthly_cancelled_amount = 0
                monthly_invoice_amount = 0
                monthly_order_amount = 0
                monthly_return_amount = 0

                today_order_amount = 0
                today_order_count = 0
                today_return_amount = 0
                today_invoice_amount = 0
                today_invoice_count = 0
                today_pending_amount = 0
                today_return_count = 0

                total_order_amount = 0
                total_pending_amount = 0
                total_cancelled_amount = 0
                total_invoice_amount = 0
                total_return_amount = 0

                monthly_completed = request.env['sale.order'].sudo().search_count([('partner_id', '=', partner_id), ('state', '=', 'sale'), ('invoice_status', '=', 'invoiced'), ('date_order','<=',month_end),('date_order','>=',month_start)])
                monthly_cancelled_orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id), ('state', '=', 'cancel'),('date_order','<=', month_end),('date_order','>=',month_start)])
                monthly_pending_orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id), ('state', '!=', 'cancel'),('date_order','<=', month_end),('date_order','>=',month_start),('invoice_status','in',['no','to_invoice'])])
                monthly_invoices = request.env['account.move'].sudo().search([('partner_id', '=',partner_id), ('state', '!=', 'cancel'),('invoice_date','<=',month_end),('invoice_date','>=',month_start)])
                monthly_returns = request.env['account.move'].sudo().search([('partner_id', '=',partner_id), ('move_type','=','out_refund'),('invoice_date','<=',month_end),('invoice_date','>=',month_start)])
                monthly_orders = request.env['sale.order'].sudo().search([('partner_id', '=',partner_id), ('state', '=', 'sale'),('date_order','<=',month_end),('date_order','>=',month_start)])
                
                for order in monthly_orders:
                    monthly_order_amount += order.amount_untaxed
                    if order.date_order.date() == date.today():
                        today_order_amount += order.amount_untaxed
                        today_order_count += 1

                for pending in monthly_pending_orders:
                    monthly_pending_amount += pending.amount_untaxed
                    if pending.date_order.date() == date.today():
                        today_pending_amount += pending.amount_untaxed
                
                for cancel in monthly_cancelled_orders:
                    monthly_cancelled_amount += cancel.amount_untaxed

                for invoice in monthly_invoices:
                    monthly_invoice_amount += invoice.amount_untaxed
                    if invoice.invoice_date == date.today():
                        today_invoice_amount += invoice.amount_untaxed
                        today_invoice_count += 1
                
                for returned in monthly_returns:
                    monthly_return_amount += returned.amount_untaxed
                    if returned.invoice_date == date.today():
                        today_return_amount += returned.amount_untaxed
                        today_return_count += 1

                monthly = {
                    'monthly_order_count': len(monthly_orders),
                    'monthly_order_amount': monthly_order_amount,
                    'monthly_completed': monthly_completed,
                    'monthly_pending_amount': round(monthly_pending_amount,2),
                    'monthly_cancelled_amount': round(monthly_cancelled_amount,2),
                    'monthly_invoice_count': len(monthly_invoices),
                    'monthly_invoice_amount': monthly_invoice_amount,
                    'monthly_return_count': len(monthly_returns),
                    'monthly_return_amount': monthly_return_amount
                }
                orders.append({'monthly':monthly})

                today_completed = request.env['sale.order'].sudo().search_count([('partner_id', '=', partner_id), ('state', '=', 'sale'), ('invoice_status', '=', 'invoiced'), ('date_order', '=', date.today())])

                today = {
                    'today_order_count': today_order_count,
                    'today_order_amount': today_order_amount,
                    'today_completed': today_completed,
                    'today_pending_amount': today_pending_amount,
                    'today_invoice_count': today_invoice_count,
                    'today_invoice_amount': today_invoice_amount,
                    'today_return_count': today_return_count,
                    'today_return_amount': today_return_amount
                }
                orders.append({'today': today})
                
                total_orders = request.env['sale.order'].sudo().search([('partner_id','=',partner_id),('state','=','sale')])
                total_cancelled_orders = request.env['sale.order'].sudo().search([('partner_id', '=',partner_id), ('state', '=', 'cancel')])
                total_pending_orders = request.env['sale.order'].sudo().search([('partner_id', '=',partner_id), ('state', '!=', 'cancel'),('invoice_status','in',['no','to_invoice'])])
                total_invoices = request.env['account.move'].sudo().search([('partner_id', '=',partner_id), ('state', '!=', 'cancel')])
                total_returns = request.env['account.move'].sudo().search([('partner_id', '=',partner_id), ('move_type','=','out_refund'), ('state', '!=', 'cancel')])
                
                for order in total_orders:
                    total_order_amount += order.amount_untaxed

                for pending in total_pending_orders:
                    total_pending_amount += pending.amount_untaxed
                
                for cancel in total_cancelled_orders:
                    total_cancelled_amount += cancel.amount_untaxed

                for invoice in total_invoices:
                    total_invoice_amount += invoice.amount_untaxed
                
                for returned in total_returns:
                    total_return_amount += returned.amount_untaxed

                total = {
                    'total_order_count': len(total_orders),
                    'total_order_amount': total_order_amount,
                    'total_pending_amount': round(total_pending_amount,2),
                    'total_cancelled_amount': round(total_cancelled_amount,2),
                    'total_invoice_count': len(total_invoices),
                    'total_invoice_amount': total_invoice_amount,
                    'total_return_count': len(total_returns),
                    'total_return_amount': total_return_amount
                }
                orders.append({'total':total})
                return response(
                    status=200,
                    message="Customer Data Fetched Successfully",
                    data=orders
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
        
    @http.route('/api/v1/customer/due', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.CUSTOMER.value])
    def customer_due(self, **kwargs):
        try:
            user_id = request.env.user.id
            # user_id = kwargs['user_id']
            user = request.env['res.users'].sudo().search([('id','=',user_id)])

            if user.partner_id:
                customer_id = user.partner_id.id
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
        
        
    @http.route('/api/v1/customer/partner-ledger', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.CUSTOMER.value])
    def customer_partner_ledger(self, **kwargs):
        try:
            user_id = request.env.user.id
            # user_id = kwargs['user_id']
            user = request.env['res.users'].sudo().search([('id','=',user_id)])

            if user.partner_id:
                customer_id = user.partner_id.id

                data = []
                total_debit = 0
                total_credit = 0
                total_balance = 0
                old_balance = 0

                move_line = request.env['account.move.line'].sudo().search([('partner_id','=',customer_id)], order='date, id desc')

                for line in move_line:
                    total_debit += line.debit
                    total_credit += line.credit

                    balance = old_balance + line.debit - line.credit
                    old_balance = round(balance,2)

                    line_details = {
                        'date': line.date,
                        'journal_entry': line.move_name,
                        'label': line.name,
                        'debit': line.debit,
                        'credit': line.credit,
                        'balance': round(balance,2),
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

    @http.route("/api/v1/customer/dashboard-orders-today", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.CUSTOMER.value])
    def customer_today_orders(self, **kwargs):
        try:
            today_start = datetime.combine(datetime.today(), datetime.min.time())
            today_end = today_start + timedelta(days=1)

            orders = request.env['sale.order'].sudo().search([
                ('partner_id', '=', request.env.user.id),
                ('date_order', '>=', today_start),
                ('date_order', '<', today_end)
            ], order='date_order desc')

            data = []
            for order in orders:
                data.append({
                    "id": order.id,
                    "order_number": order.name,
                    "customer": {
                        "id": order.partner_id.id,
                        "name": order.partner_id.name
                    },
                    "payment_method": order.payment_method if order.payment_method else "",
                    "remarks": order.remarks if order.remarks else "",
                    "subtotal": f"{order.currency_id.symbol} {order.amount_untaxed}",
                    "tax_amount": f"{order.currency_id.symbol} {order.amount_tax}",
                    "total_amount": f"{order.currency_id.symbol} {order.amount_total}",
                    "order_counts": len(order.order_line),
                    "currency": order.currency_id.symbol,
                    "order_date": order.date_order.date(),
                    "invoice_status": order.invoice_status,
                    "state": order.state
                })

            return response(
                status=200,
                message="Today Orders Fetched Successfully",
                data=data
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

    @http.route("/api/v1/customer/dashboard-orders-monthly", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.CUSTOMER.value])
    def customer_monthly_orders(self, **kwargs):
        try:
            date_to = calendar.monthrange(date.today().year, date.today().month)
            month_start = str(date.today().year) + "-" + str(date.today().month) + "-01"
            month_end = str(date.today().year) + "-" + str(date.today().month) + "-" + str(date_to[1])

            orders = request.env['sale.order'].sudo().search(
                [('partner_id', '=', request.env.user.id),
                ('date_order','<=',month_end),
                ('date_order','>=',month_start)],
                order='date_order desc'  
            )

            data = []
            for order in orders:
                data.append({
                    "id": order.id,
                    "order_number": order.name,
                    "customer": {
                        "id": order.partner_id.id,
                        "name": order.partner_id.name
                    },
                    "payment_method": order.payment_method if order.payment_method else "",
                    "remarks": order.remarks if order.remarks else "",
                    "subtotal": f"{order.currency_id.symbol} {order.amount_untaxed}",
                    "tax_amount": f"{order.currency_id.symbol} {order.amount_tax}",
                    "total_amount": f"{order.currency_id.symbol} {order.amount_total}",
                    "order_counts": len(order.order_line),
                    "currency": order.currency_id.symbol,
                    "order_date": order.date_order.date(),
                    "invoice_status": order.invoice_status,
                    "state": order.state
                })

            return response(
                status=200,
                message="Monthly Orders Fetch Successfully",
                data=data
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