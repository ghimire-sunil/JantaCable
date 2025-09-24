from pydantic import ValidationError
from .utils import (
    ALLOWED_URL,
    response,
    required_login,
    formate_error,
    check_role,
    UserRole,
)
from odoo.http import request, Response
from odoo import http, Command
from .schema.distributer_order import DOFilter, DistributorOrder, CompleteOrderPayload
from .schema.order import GetOrder
from .schema.contacts import Contacts
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class DistributorOrderController(http.Controller):
    @http.route(
        "/api/v1/distributor/create-order",
        type="json",
        auth="public",
        csrf=False,
        cors=ALLOWED_URL,
    )
    @required_login
    def create_order(self, **kwargs):
        try:
            order = DistributorOrder(**kwargs)

            customer = (
                request.env["res.partner"]
                .sudo()
                .search([("id", "=", int(order.partner_id))], limit=1)
            )

            if not customer:
                raise Exception("Customer Not Found.")
            
            if order.discount_type and not order.discount_amount:
                raise Exception("Please give discount amount!")
            
            if order.discount_type == "Percent":
                if order.discount_amount > 100:
                    raise Exception("Percent Discount cannot be more than a 100!!")

            order_line = []
            products = order.products
            for product_line in products:
                product = (
                    request.env["product.product"]
                    .sudo()
                    .search([("id", "=", product_line.product_id)], limit=1)
                )

                if not product:
                    raise Exception("Product Not Found")

                order_line.append(
                    Command.create(
                        {
                            "product_id": product.id,
                            "qty": product_line.qty,
                        }
                    )
                )

            new_order = (
                request.env["distributor.order"]
                .sudo()
                .create(
                    {
                        "partner_id": customer.id,
                        "user_id": request.env.user.id,
                        "order_line_ids": order_line,
                    }
                )
            )
            new_order._action_confirm()

            return {
                "result": {
                    "status": 200,
                    "message": "Order created successfully!!",
                    "data": {"order_id": new_order.id},
                }
            }
        except ValidationError as error:
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors()),
            )
        except Exception as e:
            return response(status=400, message=e.args[0], data=None)

    @http.route(
        "/api/v1/distributor/orders",
        type="json",
        auth="public",
        csrf=False,
        cors=ALLOWED_URL,
    )
    @required_login
    def get_orders(self, **kwargs):
        domain = []
        try:
            filter = DOFilter(**kwargs)

            if filter.state:
                domain.append(("state", "=", filter.state))

            if filter.order_date:
                domain.append(("order_date", "=", filter.order_date))

            page = filter.page or 1
            limit = filter.limit or 80

            # distributor
            if request.env.user.role == "customer":
                domain.append(("distributor_id", "=", request.env.user.partner_id.id))

            # sales
            elif request.env.user.role == "sale_person":
                domain.append(("user_id", "=", request.env.user.id))

            elif request.env.user.role == "sale_agent":
                if not filter.salesperson_id:
                    raise Exception("Please specify a salesperson!!")
                domain.append(("user_id", "=", filter.salesperson_id))

            orders = (
                request.env["distributor.order"]
                .sudo()
                .search(
                    domain=domain,
                    order="order_date desc",
                    offset=(page - 1) * limit,
                    limit=limit,
                )
            )

            total_count = (
                request.env["distributor.order"]
                .sudo()
                .search_count(
                    domain=domain,
                )
            )
            data = []
            for order in orders:
                data.append(
                    {
                        "id": order.id,
                        "order_number": order.name,
                        "customer": {
                            "id": order.partner_id.id,
                            "name": order.partner_id.name,
                        },
                        "order_counts": len(order.order_line_ids),
                        "order_date": order.order_date.isoformat(),
                        "state": order.state,
                    }
                )

            return response(
                status=200,
                message="Fetched Successfully",
                data={"total_count": total_count, "orders": data},
            )

        except ValidationError as error:
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors()),
            )
        except Exception as e:
            return response(status=400, message=e.args[0], data=None)

    @http.route(
        "/api/v1/distributor/order-detail",
        type="json",
        auth="public",
        csrf=False,
        cors=ALLOWED_URL,
    )
    @required_login
    def order_detail(self, **kwargs):
        try:
            get_order = GetOrder(**kwargs)

            order = (
                request.env["distributor.order"]
                .sudo()
                .search([("id", "=", get_order.order_id)], limit=1)
            )

            if not order:
                raise Exception("Order Not Found")

            lines = []

            for line in order.order_line_ids:
                lines.append(
                    {
                        "id": line.id,
                        "product": {
                            "id": line.product_id.id,
                            "name": line.product_id.name,
                        },
                        "qty": line.qty,
                    }
                )

            data = {
                "id": order.id,
                "order_number": order.name,
                "customer": {
                    "id": order.partner_id.id,
                    "name": order.partner_id.name,
                    "address": order.partner_id.street,
                    "city": order.partner_id.city,
                    "phone": order.partner_id.phone or "N/A",
                    "mobile": order.partner_id.mobile or "N/A",
                },
                "lines": lines,
                "state": order.state,
            }
            return response(status=200, message="Order Fetch Success", data=data)

        except ValidationError as error:
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors()),
            )
        except Exception as e:
            return response(status=400, message=e.args[0], data=None)

    @http.route(
        "/api/v1/distributor/complete-order",
        type="json",
        auth="public",
        csrf=False,
        cors=ALLOWED_URL,
    )
    @required_login
    @check_role([UserRole.CUSTOMER.value])
    def complete_order(self, **kwargs):
        try:
            payload = CompleteOrderPayload(**kwargs)

            order = (
                request.env["distributor.order"]
                .sudo()
                .search([("id", "=", payload.order_id)], limit=1)
            )

            if not order:
                raise Exception("Order Not Found")

            if order.distributor_id.id != request.env.user.partner_id.id:
                raise Exception("You are not allowed to complete this order !!")

            for line in payload.lines:
                request.env["distributor.order.line"].sudo().browse(line.line_id).write(
                    {"delivered_qty": line.qty, "delivery_status": "completed"}
                )

            order.action_complete()

            return response(
                status=200,
                message="Order Completed Successfully !!",
                data={"order_id": order.id},
            )

        except ValidationError as error:
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors()),
            )
        except Exception as e:
            return response(status=400, message=e.args[0], data=None)
        
        
    @http.route('/api/v1/distributors', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @check_role([UserRole.SALE_AGENT.value])
    @required_login
    def get_distributors(self, **kwargs):
        try:
            customer = Contacts(**kwargs)

            page = customer.page or 1
            limit = customer.limit or 100
            offset = (page - 1) * limit
            search_query = customer.search_query

            domain = [("category_id.distributor","=",True)]

            # if customer.customer_id:
            #     domain += [('id','=',customer.customer_id),("category_id.distributor", "=", True)]

            if search_query and isinstance(search_query,str):
                search_query = search_query.strip().lower()
                domain += ['|', ('name', 'ilike', search_query), ('phone', 'ilike', search_query)]
          
            contacts = request.env['res.partner'].sudo().search(domain,offset=offset, limit=limit)

            data = []
            for contact in contacts:
                data.append({
                    "id": contact.id,
                    "name": contact.name,
                    "phone": contact.phone,
                    "mobile": contact.mobile,
                    "address": contact.contact_address_complete,
                    "latitude": contact.partner_latitude,
                    "longitude": contact.partner_longitude,
                    "pan_no": contact.vat,
                    "email": contact.email,
                    "due_amount": contact.credit
                })

            return response(
                status=200,
                message="Distributors Fetched Successfully",
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
        

    @http.route('/api/v1/distributor-customers', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @check_role([UserRole.SALE_AGENT.value])
    @required_login
    def get_distributor_customers(self, **kwargs):
        try:
            customer = Contacts(**kwargs)

            page = customer.page or 1
            limit = customer.limit or 100
            offset = (page - 1) * limit
            search_query = customer.search_query

            if not customer.customer_id:
                raise Exception("Distributor ID required!!")

            domain = [("distributor_id","=",customer.customer_id)]

            # if customer.customer_id:
            #     domain += [('id','=',customer.customer_id),("category_id.distributor", "=", True)]

            if search_query and isinstance(search_query,str):
                search_query = search_query.strip().lower()
                domain += ['|', ('name', 'ilike', search_query), ('phone', 'ilike', search_query)]
          
            contacts = request.env['res.partner'].sudo().search(domain,offset=offset, limit=limit)

            data = []
            for contact in contacts:
                data.append({
                    "id": contact.id,
                    "name": contact.name,
                    "phone": contact.phone,
                    "mobile": contact.mobile,
                    "address": contact.contact_address_complete,
                    "latitude": contact.partner_latitude,
                    "longitude": contact.partner_longitude,
                    "pan_no": contact.vat,
                    "email": contact.email,
                    "due_amount": contact.credit
                })

            return response(
                status=200,
                message="Distributor's Customers Fetched Successfully",
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

