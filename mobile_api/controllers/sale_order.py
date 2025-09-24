from pydantic import ValidationError
from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from odoo.http import request, Response
from odoo import http, Command
from .schema.order import Order, GetOrder, GetOrders, EditOrder, SavePayment, CancelOrder, DueOrders, GetDueOrders
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64
import json

class ProductController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/order', type='http', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value, UserRole.CUSTOMER.value])
    @make_response
    def order(self, **kwargs):
        try:
            order = Order(**kwargs)
            
            if request.env.user.role in ['sale_agent', 'sale_person']:
                if not order.customer:
                    raise Exception("Please specify a customer!")
                customer = request.env['res.partner'].sudo().search([
                    ('id', '=', int(order.customer))
                ], limit=1)
                salesperson = request.env.user.id
                
            else:
                customer = request.env['res.partner'].sudo().search([
                    ('user_ids', 'in', request.env.user.id)
                ], limit=1)
                salesperson = customer.user_id.id

            if not customer:
                raise Exception("Customer Not Found.")

            sale_order_line = []
            products = json.loads(order.products)
            for product in products:
                product_temp = request.env['product.product'].sudo().search([
                    ('id', '=', product['product_id'])
                ], limit=1)

                if not product_temp:
                    raise Exception("Product Not Found")

                sale_order_line.append(Command.create({
                    "product_id": product_temp.id,
                    "product_uom_qty": product['qty'],
                    'price_unit': product_temp.list_price
                }))

            image_ids = []
            images = request.httprequest.files.getlist('images')

            for image in images:
                image_base64 = base64.b64encode(image.read())
                image_id = request.env['sale.image'].create({
                    'name': image.filename,
                    'image_1920': image_base64
                })
                image_ids.append(image_id.id)

            new_order = request.env['sale.order'].sudo().create({
                "partner_id": customer.id,
                "user_id": salesperson,
                "order_line": sale_order_line,
                "remarks": order.remarks,
                "payment_method": order.payment_method,
                "latitude": float(order.latitude),
                "longitude": float(order.longitude),
                "order_image_ids": [id for id in image_ids]
            })
            print(customer.id)

            discount = json.loads(order.discount) if order.discount != '0' else False

            if discount:
                discount_vals = request.env['sale.order.discount'].sudo().create({
                    'sale_order_id': new_order.id,
                    'discount_type': discount['discount_type'],
                    'discount_percentage': float(discount['discount_percentage']/100) if discount['discount_percentage'] !=0 else None
                })
                discount_vals.action_apply_discount()

            customer.is_ordered_today = True

            return  {
                'result':{ 
                    "status":200,
                    "message":'Sale order created successfully!!',
                    "data": {
                        'order_id': new_order.id
                    }
                }
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

    @http.route("/api/v1/my-orders", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def my_orders(self, **kwargs):
        try:
            get_order = GetOrders(**kwargs)

            ORDER_STATUS_MAPPING = {
                'pending': ['draft', 'sent'],
                'completed': ['sale'],
                'cancelled': ['cancel']
            }

            domain = []
            if request.env.user.role == 'customer':
                domain = [
                    ('partner_id', '=', request.env.user.partner_id.id),
                    ('state', 'in', ORDER_STATUS_MAPPING.get(get_order.status))
                ]

            elif request.env.user.role in ['sale_person', 'sale_agent']:
                domain = [
                    ('user_id', '=', request.env.user.id),
                    ('state', 'in', ORDER_STATUS_MAPPING.get(get_order.status))
                ]
                if get_order.customer:
                    domain.append(('partner_id', '=', get_order.customer))

            orders = request.env['sale.order'].sudo().search(
                domain=domain,
                order='date_order desc'  
            )

            can_edit = True if get_order.status == 'pending' else False

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
                    "can_edit": can_edit,
                    "order_counts": len(order.order_line),
                    "currency": order.currency_id.symbol,
                    "order_date": order.date_order.date(),
                    "invoice_status": order.invoice_status
                })

            return response(
                status=200,
                message="Sale Order Fetch Successfully",
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

    @http.route("/api/v1/order-detail", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def order_detail(self, **kwargs):
        try:
            get_order = GetOrder(**kwargs)

            order = request.env['sale.order'].sudo().search([
                ('id', '=', get_order.order_id)
            ], limit=1)

            if not order:
                raise Exception("Order Not Found")          
                
            # if not (order.user_id.id == request.env.user.id or request.env.user.role == 'sale_agent'):              
            #     raise Exception("You Dont Have Access to View this Order")

            can_edit = True if order.state in ['draft', 'sent'] else False  

            lines = []
            for line in order.order_line:
                lines.append({      
                    "id": line.id,
                    "product": {
                        "id": line.product_id.id,
                        "name": line.product_id.name
                    },
                    "name": line.name,
                    "qty": line.product_uom_qty,
                    "unit": line.product_uom.name,
                    "price_unit": f"{line.currency_id.symbol} {line.price_unit}",
                    "amount": f"{line.currency_id.symbol} {line.price_subtotal}",
                    "currency": line.currency_id.symbol
                })
                
            if order.state in ['draft', 'sent']:
                order_status = "Pending"
            elif order.state == 'sale':
                order_status = "Confirm"
            else:
                order_status = 'Cancel'
                

            total_amount = order.amount_total
            total_paid = sum(request.env['account.payment'].sudo().search([
                ('sale_order_id', '=', order.id)
            ]).mapped('amount'))
            remaining_amount = total_amount - total_paid
            
            actual_remaining_amount = 0
            if remaining_amount > 0:
                is_fully_paid = False
                actual_remaining_amount = remaining_amount
            else:
                remaining_amount = 0
                is_fully_paid = True

            payments = []
            for invoice in order.invoice_ids:
                for payment in invoice.matched_payment_ids:
                    payments.append({
                        "id": payment.id,
                        "amount": payment.amount,
                        "journal": payment.journal_id.name,
                        "date": payment.date,
                        "memo": payment.memo
                    })
            
            
            data = {
                "id": order.id,
                "order_number": order.name,
                "customer": {
                    "id": order.partner_id.id,
                    "name": order.partner_id.name
                },
                "payment_method": order.payment_method if order.payment_method else "",
                "remarks": order.remarks if order.remarks else "",
                "lines": lines,
                "subtotal": f"{order.currency_id.symbol} {order.amount_untaxed}",
                "tax_amount": f"{order.currency_id.symbol} {order.amount_tax}",
                "total_amount": f"{order.currency_id.symbol} {order.amount_total}",
                "can_edit": can_edit,
                "status": order_status,
                "order_counts": len(order.order_line),
                "currency": order.currency_id.symbol,
                "order_date": order.date_order.date(),
                "total_amount_in_float": order.amount_total,
                "remaining_amount": f"{order.currency_id.symbol} {actual_remaining_amount}",
                "remaining_amount_in_float": actual_remaining_amount,
                "is_fully_paid": is_fully_paid,
                "invoice_status": order.invoice_status,
                "payment": payments
            }

            return response(
                status=200,
                message="Sale Order Fetch Successfully",
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

    @http.route('/api/v1/update-order', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def update_order(self, **kwargs):
        try:
            edit_order = EditOrder(**kwargs)
            
            order = request.env['sale.order'].sudo().search([
                ('id', '=', edit_order.order_id)
            ], limit=1)

            if not order:
                raise Exception("Order Not Found")

            # if not order.user_id.id == request.env.user.id or not request.env.user.role == 'sale_agent':
            #     raise Exception("You Dont Have Access to Modify this Order")
            
            if not order.state in ['draft', 'sent']:
                raise Exception("You cannot update confirm order")
            
            # order.write({
            #     "remarks": edit_order.remarks,
            #     "payment_method": edit_order.payment_method,
            # })
            
            # order_lines = order.order_line
            
            order.order_line.unlink()
            sale_order_line = []
            for line in edit_order.lines:
                # order_line = order_lines.filtered(lambda l: l.id == line.line_id)
                # if not order_line:
                #     raise Exception(f"Order Line with  ID {line.line_id} is not Found.")
                product = request.env['product.product'].sudo().search([
                    ('id', '=', line.product_id)
                ], limit=1)
                
                if not product:
                    raise Exception(f"Product with if {line.product_id} not Found.")
                
                sale_order_line.append(Command.create({
                    "product_id": product.id,
                    "product_uom_qty": line.qty,
                    'price_unit': product.list_price    
                }))
            
            order.write({
                "order_line": sale_order_line,
            })
        
            return response(
                status=200,
                message="Sale Order Updated Successfully",
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
    
    @http.route('/api/v1/save-payment', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def sale_payment(self, **kwargs):
        try:
            payments = SavePayment(**kwargs)

            order = request.env['sale.order'].sudo().search([
                ('id', '=', payments.order_id)
            ], limit=1) 

            if not order:
                raise Exception("Order Not Found")
            
            for payment in payments.payments:
                journal_code_mapping = {
                    "cheque": "CQ", 
                    "fonepay": "FP",
                    "cash":  "CSH1"
                }
                                
                journal_code = journal_code_mapping.get(payment.payment_method, "CSH1")

                journal  = request.env['account.journal'].search([
                    ("code", '=', journal_code)
                ],limit=1)
                if not journal:
                    raise Exception("Journal is not Set Properly. Please Contact Admin.")

                # payment_state = self.env['ir.config_parameter'].sudo().get_param('api.manual_payment')
                # status = 'paid'
                # if payment_state:
                #     status = 'draft'
                
                request.env['account.payment'].sudo().create({
                    "payment_type": 'inbound',
                    "partner_id": order.partner_id.id,
                    "amount": payment.amount,
                    "date": date.today(),
                    "memo": payment.remarks,
                    "journal_id": journal.id,
                    "sale_order_id": order.id,
                    # "state": status
                })              

            return response(
                status=200,
                message="Payment Save Successfully",
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

    @http.route('/api/v1/order/cancel', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def cancel_order(self, **kwargs):
        try:
            cancel_order = CancelOrder(**kwargs)

            order = request.env['sale.order'].sudo().search([
                ('id', '=', cancel_order.order_id)
            ], limit=1)

            if not order:
                raise Exception("Order Not Found")

            # if not order.user_id.id == request.env.user.id or not request.env.user.role == 'sale_agent':
            #     raise Exception("You Dont Have Access to Modify this Order")

            if not order.state in ['draft', 'sent']:
                raise Exception("You cannot update confirm order")
            
            if not order.remarks:
                order.remarks = "Cancelled: " + kwargs['remarks']
            else:
                order.remarks = order.remarks + "\n Cancelled: " + kwargs['remarks']

            order.action_cancel()

            return response(
                status=200,
                message="Sale Order Cancel Successfully",
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
        
    @http.route('/api/v1/due-orders', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def due_orders(self, **kwargs):
        try:
            due_order = DueOrders(**kwargs)
            salesperson_id = request.env.user.id
            order_list = []

            customer = request.env['res.partner'].sudo().search([
                ('id', '=', due_order.customer_id)
            ], limit=1)
            if not customer:
                raise Exception("Customer Not Found.")

            orders = request.env['sale.order'].sudo().search([
                ('partner_id','=',customer.id),
                ('invoice_status', 'in', ['invoiced','to invoice'])
            ])
            if not orders:
                raise Exception("No orders found")

            for order in orders:
                invoices = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.payment_state not in ['paid', 'invoicing_legacy', 'reversed', 'blocked', 'in_payment', 'partial'] and inv.state=='posted')

                total_due = sum(invoice.amount_residual for invoice in invoices)
                total_paid = sum(payment.amount for payment in invoices.matched_payment_ids)
                due = total_due - total_paid
                order_date = order.date_order.date()
                difference = date.today() - order_date

                if due > 0: 
                    order_list.append({
                        'order_id': order.id,
                        'sales_order': order.name,
                        'amount_due': due,
                        'days': str(difference.days) + " days ago",
                        'invoice_status': order.invoice_status,
                        'invoices': [
                            {
                                'name': invoice.name, 
                                'invoice_date': invoice.invoice_date, 
                                'amount_due': invoice.amount_residual - sum(payment.amount for payment in invoice.matched_payment_ids)
                            } 
                            for invoice in invoices]
                    })

            return response(
                status=200,
                message="Sale Orders Fetched Successfully",
                data=order_list
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

       
    @http.route("/api/v1/get-orders", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def get_orders(self, **kwargs):
        try:
            params = GetDueOrders(**kwargs)
            user = request.env.user
                        
            partner_id = request.env.user.partner_id.id
            domain = [('user_id', '=', user.id),
                    ('invoice_status', 'in', ['invoiced','to invoice']),
                    ('invoice_ids', '!=', [])]
            if params.customer_id and params.customer_id != partner_id:
                partner_id = params.customer_id
                domain.append(('partner_id','=', partner_id))
            unsorted_orders = request.env['sale.order'].sudo().search(
                    domain=domain,
                    order='date_order desc'  
                )
            orders = sorted(unsorted_orders, key=lambda l: l.invoice_ids[0].invoice_date)
            data = []
            for order in orders:

                invoices = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.payment_state not in ['reversed', 'blocked'] and inv.state=='posted')
                total_due = sum(invoice.amount_residual for invoice in invoices)
                total_paid = sum(payment.amount for payment in invoices.matched_payment_ids)

                due = 0
                if total_due != 0:
                    due = total_due - total_paid
                order_date = order.date_order.date()
                difference = date.today() - order_date

                if invoices:
                    data.append({
                        "id": order.id,
                        "order_number": order.name,
                        "customer": {
                            "id": order.partner_id.id,
                            "name": order.partner_id.name
                        },
                        "payment_method": order.payment_method if order.payment_method else "",
                        "remarks": order.remarks if order.remarks else "",
                        "subtotal": order.amount_untaxed,
                        "tax_amount": order.amount_tax,
                        "total_amount": order.amount_total,
                        "amount_paid": total_paid,
                        "amount_due": due,
                        "order_counts": len(order.order_line),
                        "currency": order.currency_id.symbol,
                        "order_date": order.date_order.date(),
                        "invoice_status": order.invoice_status,
                        "state": order.state
                    })

            return response(
                status=200,
                message="Sale Order Fetch Successfully",
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

        
    @http.route("/api/v1/filter-orders", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def get_filtered_orders(self, **kwargs):
        try:
            filter_value = kwargs.get('filter_value')
            date_from = kwargs.get('filter_date_from')
            date_to = kwargs.get('filter_date_to')
            partner = request.env.user.partner_id.id

            if filter_value:
                date_to = datetime.now()
                if filter_value == "7 Days":
                    date_from = date_to - timedelta(days=7)
                if filter_value == "14 Days":
                    date_from = date_to - timedelta(days=14)
                if filter_value == "30 Days":
                    date_from = date_to - relativedelta(months=1)

            orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner), '&', ('date_order','<=',date_to), ('date_order', '>=', date_from)], order="date_order desc")
            data = []
            for order in orders:
                invoices = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.payment_state not in ['reversed', 'blocked'] and inv.state=='posted')
                total_due = sum(invoice.amount_residual for invoice in invoices)
                total_paid = sum(payment.amount for payment in invoices.matched_payment_ids)

                due = 0
                if total_due != 0:
                    due = total_due - total_paid
                order_date = order.date_order.date()
                difference = date.today() - order_date
                if invoices:
                    data.append({
                        "id": order.id,
                        "order_number": order.name,
                        "customer": {
                            "id": order.partner_id.id,
                            "name": order.partner_id.name
                        },
                        "payment_method": order.payment_method if order.payment_method else "",
                        "remarks": order.remarks if order.remarks else "",
                        "subtotal": order.amount_untaxed,
                        "tax_amount": order.amount_tax,
                        "total_amount": order.amount_total,
                        "amount_paid": total_paid,
                        "amount_due": due,
                        "order_counts": len(order.order_line),
                        "currency": order.currency_id.symbol,
                        "order_date": order.date_order.date(),
                        "invoice_status": order.invoice_status,
                        "state": order.state
                    })        

            return response(
                status=200,
                message="Sale Orders Fetched Successfully",
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
