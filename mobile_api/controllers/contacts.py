import uuid
from odoo import http
from odoo.http import request
from .utils import ALLOWED_URL, response, required_login, formate_error
from .schema.contacts import Contacts, ContactDetail, OrderHistory
from .schema.location import PartnerLocation
from pydantic import ValidationError
from datetime import datetime

class ContactController(http.Controller):

    @http.route('/api/v1/contacts', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def get_contacts(self, **kwargs):
        try:
            customer = Contacts(**kwargs)

            page = customer.page or 1
            limit = customer.limit or 100
            offset = (page - 1) * limit
            search_query = customer.search_query

            domain = [("category_id.customer", "=", True)]

            if customer.customer_id:
                domain += [('id','=',customer.customer_id)]

            if search_query and isinstance(search_query,str):
                search_query = search_query.strip().lower()
                domain += ['|', ('name', 'ilike', search_query), ('phone', 'ilike', search_query)]
          
            contacts = request.env['res.partner'].sudo().search(domain,offset=offset, limit=limit)

            data = []
            for contact in contacts:
                orders = request.env['sale.order'].sudo().search([('partner_id','=',contact.id),('state','=','sale')])

                owner = []
                other_contacts = []
                for child in contact.child_ids:
                    credit_summary = {
                        'credit_limit': child.credit_limit,
                        'credit_used': child.credit,
                        'credit_days': child.credit_limit_span,
                        'credit_limit_exceeded': True if child.credit > child.credit_limit else False,
                        'credit_days_exceeded': child.credit_limit_span_exceeded
                    }
                    if child.function == "Owner":
                        owner.append({
                            "id": child.id,
                            "name": child.name,
                            "phone": child.phone,
                            "mobile": child.mobile,
                            "address": child.contact_address_complete,
                            "latitude": child.partner_latitude,
                            "longitude": child.partner_longitude,
                            "credit_limit": credit_summary
                        })
                    else:
                        other_contacts.append({
                            "id": child.id,
                            "name": child.name,
                            "phone": child.phone,
                            "mobile": child.mobile,
                            "address": child.contact_address_complete,
                            "latitude": child.partner_latitude,
                            "longitude": child.partner_longitude,
                            "credit_limit": credit_summary
                        })

                tags = request.env['res.partner.category'].sudo().search([('mobile_ok','=',True)])
                tag_list = []
                for tag in contact.category_id:
                    if tag in tags:
                        tag_list.append({
                            'id': tag.id,
                            'name': tag.name
                        })

                # due_amount = 0
                # due_orders = request.env['sale.order'].sudo().search([
                #     ('partner_id','=',contact.id),
                #     ('invoice_status', 'in', ['invoiced','to invoice'])
                # ])
                # for order in due_orders:
                #     invoices = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.payment_state not in ['paid', 'invoicing_legacy', 'reversed', 'blocked', 'in_payment'] and inv.state=='posted')

                #     total_due = sum(invoice.amount_residual for invoice in invoices)
                #     total_paid = sum(payment.amount for payment in invoices.matched_payment_ids)
                #     due = total_due - total_paid
                #     due_amount += due

                credit_summary = {
                    'credit_limit': contact.credit_limit,
                    'credit_used': contact.credit,
                    'credit_days': contact.credit_limit_span,
                    'credit_limit_exceeded': True if contact.credit > contact.credit_limit else False,
                    'credit_days_exceeded': contact.credit_limit_span_exceeded
                }

                data.append({
                    "id": contact.id,
                    "name": contact.name,
                    "owner": owner,
                    "phone": contact.phone,
                    "mobile": contact.mobile,
                    "address": contact.contact_address_complete,
                    "latitude": contact.partner_latitude,
                    "longitude": contact.partner_longitude,
                    "tags": tag_list,
                    "credit_summary": credit_summary,
                    "pan_no": contact.vat,
                    "email": contact.email,
                    "total_orders": len(orders),
                    "due_amount": contact.credit,
                    "contacts": other_contacts
                })

            return response(
                status=200,
                message="Contacts Fetched Successfully",
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
    

    @http.route('/api/v1/contact-detail', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def get_contact_detail(self, **kwargs):
        try:
            customer = ContactDetail(**kwargs)
          
            contact = request.env['res.partner'].sudo().search([('id','=',customer.customer_id),("category_id.customer", "=", True)],limit=1)   

            if not contact:
                raise Exception("No customer found!!")
                     
            orders = request.env['sale.order'].sudo().search([('partner_id','=',contact.id),('state','=','sale')])

            owner = []
            other_contacts = []
            for child in contact.child_ids:
                credit_summary = {
                    'credit_limit': child.credit_limit,
                    'credit_used': child.credit,
                    'credit_days': child.credit_limit_span,
                    'credit_limit_exceeded': True if child.credit > child.credit_limit else False,
                    'credit_days_exceeded': child.credit_limit_span_exceeded
                }
                if child.function == "Owner":
                    owner.append({
                        "id": child.id,
                        "name": child.name,
                        "phone": child.phone,
                        "mobile": child.mobile,
                        "address": child.contact_address_complete,
                        "latitude": child.partner_latitude,
                        "longitude": child.partner_longitude,
                        "credit_limit": credit_summary
                    })
                else:
                    other_contacts.append({
                        "id": child.id,
                        "name": child.name,
                        "phone": child.phone,
                        "mobile": child.mobile,
                        "address": child.contact_address_complete,
                        "latitude": child.partner_latitude,
                        "longitude": child.partner_longitude,
                        "credit_limit": credit_summary
                    })

            tags = request.env['res.partner.category'].sudo().search([('mobile_ok','=',True)])
            tag_list = []
            for tag in contact.category_id:
                if tag in tags:
                    tag_list.append({
                        'id': tag.id,
                        'name': tag.name
                    })

                # due_amount = 0
                # due_orders = request.env['sale.order'].sudo().search([
                #     ('partner_id','=',contact.id),
                #     ('invoice_status', 'in', ['invoiced','to invoice'])
                # ])
                # for order in due_orders:
                #     invoices = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.payment_state not in ['paid', 'invoicing_legacy', 'reversed', 'blocked', 'in_payment'] and inv.state=='posted')

                #     total_due = sum(invoice.amount_residual for invoice in invoices)
                #     total_paid = sum(payment.amount for payment in invoices.matched_payment_ids)
                #     due = total_due - total_paid
                #     due_amount += due

            credit_summary = {
                'credit_limit': contact.credit_limit,
                'credit_used': contact.credit,
                'credit_days': contact.credit_limit_span,
                'credit_limit_exceeded': True if contact.credit > contact.credit_limit else False,
                'credit_days_exceeded': contact.credit_limit_span_exceeded
            }

            data = {
                "id": contact.id,
                "name": contact.name,
                "owner": owner,
                "phone": contact.phone,
                "mobile": contact.mobile,
                "address": contact.contact_address_complete,
                "latitude": contact.partner_latitude,
                "longitude": contact.partner_longitude,
                "tags": tag_list,
                "credit_summary": credit_summary,
                "pan_no": contact.vat,
                "email": contact.email,
                "total_orders": len(orders),
                "due_amount": contact.credit,
                "contacts": other_contacts
            }

            return response(
                status=200,
                message="Contacts Fetched Successfully",
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
        

    @http.route('/api/v1/saleperson-location', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def get_saleperson_location(self, **kwargs):
        try:
            location = PartnerLocation(**kwargs)

            # current_date = datetime.fromisoformat(location.date)

            request.env['partner.location'].sudo().create({
                'partner_id': request.env.user.partner_id.id,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'date': datetime.now()
            })

            return response(
                    status=200,
                    message="Location Saved Successfully!",
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
        
    @http.route("/api/v1/order-history", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def order_history(self, **kwargs):
        try:
            history = OrderHistory(**kwargs)

            ORDER_STATUS_MAPPING = {
                'pending': ['draft', 'sent'],
                'completed': ['sale'],
                'cancelled': ['cancel']
            }

            orders = request.env['sale.order'].sudo().search(
                [('partner_id', '=', history.user_id), ('state', 'in', ORDER_STATUS_MAPPING.get(history.status))],
                order='date_order desc'  
            )

            can_edit = True if history.status == 'pending' else False

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
        
    @http.route("/api/v1/salesperson-order-history", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def salesperson_order_history(self, **kwargs):
        try:
            history = OrderHistory(**kwargs)

            ORDER_STATUS_MAPPING = {
                'pending': ['draft', 'pending', 'assigned'],
                'completed': ['completed'],
                'cancelled': ['cancelled']
            }

            orders = request.env['distributor.order'].sudo().search(
                [('user_id', '=', history.user_id), ('state', 'in', ORDER_STATUS_MAPPING.get(history.status))],
                order='order_date desc'  
            )

            can_edit = True if history.status == 'pending' else False

            data = []
            for order in orders:
                data.append({
                    "id": order.id,
                    "order_number": order.name,
                    "customer": {
                        "id": order.partner_id.id,
                        "name": order.partner_id.name
                    },
                    "order_counts": len(order.order_line_ids),
                    "order_date": order.order_date,
                    "state": order.state,
                    "distributor": order.distributor_id.name,
                    "can_edit": can_edit
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