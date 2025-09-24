from odoo import http, fields
from odoo.http import request
from pydantic import ValidationError
from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from .schema.order import GetOrders
from .schema.contacts import OrderHistoryDaily
from datetime import date, datetime, timedelta
import calendar

class DashboardController(http.Controller):

    @http.route('/api/v1/dashboard', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def salesperson_dashboard(self, **kwargs):
        try:
            salesperson_id = request.env.user.id

            orders = []
            active_plan = request.env['sale.commission.plan'].sudo().search([("date_from", "<", fields.Datetime.now()), ("date_to", ">", fields.Datetime.now())])
            active_plan_ids = active_plan.ids
            sales_commission_report = request.env['sale.commission.report'].sudo().search([("plan_id", "in", active_plan_ids), ('user_id','=',salesperson_id)])
            month_start = str(date.today().year) + "-" + str(date.today().month) + "-01"

            pending = 0
            cancelled = 0
            today_pending = 0
            today_achieved = 0
            today_achieve_percent = 0
            invoice_amount = 0
            today_invoice_amount = 0
            return_amount = 0
            today_return_amount = 0
            today_invoice = 0
            today_return = 0

            months = [report.date_to.month for report in sales_commission_report]

            if date.today().month not in months:
                raise Exception("Please create a commission plan for the target month!")

            for report in sales_commission_report:
                if report.date_to.month == date.today().month:
                    if report.target_amount:
                        completed = round(report.achieved,2)
                        target = round(report.target_amount,2)
                        achievement = round(report.achieved,2)
                        today_order = round(report.target_amount / report.date_to.day,2)
                        monthly_order_count = request.env['sale.order'].sudo().search_count([('user_id', '=',salesperson_id), ('state', '=', 'sale'),('date_order','<=',report.date_to),('date_order','>=',month_start)])
                        cancelled_orders = request.env['sale.order'].sudo().search([('user_id', '=',salesperson_id), ('state', '=', 'cancel'),('date_order','<=',report.date_to),('date_order','>=',month_start)])
                        pending_orders = request.env['sale.order'].sudo().search([('user_id', '=',salesperson_id), ('state', '!=', 'cancel'),('date_order','<=',report.date_to),('date_order','>=',month_start),('invoice_status','in',['no','to_invoice'])])
                        invoices = request.env['account.move'].sudo().search([('user_id', '=',salesperson_id), ('state', '!=', 'cancel'),('invoice_date','<=',report.date_to),('invoice_date','>=',month_start)])
                        returns = request.env['account.move'].sudo().search([('user_id', '=',salesperson_id), ('move_type','=','out_refund'),('invoice_date','<=',report.date_to),('invoice_date','>=',month_start)])
                        break
                    else:
                        raise Exception("Please choose a target amount in your commissions!")     

            for order in pending_orders:
                pending += order.amount_untaxed
                if order.date_order.date() == date.today():
                    today_pending += order.amount_untaxed
            
            for cancel in cancelled_orders:
                cancelled += cancel.amount_untaxed

            for invoice in invoices:
                invoice_amount += invoice.amount_untaxed
                if invoice.invoice_date == date.today():
                    today_invoice_amount += invoice.amount_untaxed
                    today_invoice += 1
            
            for returned in returns:
                return_amount += returned.amount_untaxed
                if returned.invoice_date == date.today():
                    today_return_amount += returned.amount_untaxed
                    today_return += 1
            
            monthly = {
                'monthly_completed': completed,
                'monthly_pending': round(pending,2),
                'monthly_cancelled': round(cancelled,2),
                'monthly_order_count': monthly_order_count, 
                'monthly_invoice_count': len(invoices),
                'monthly_invoice_amount': invoice_amount,
                'monthly_return_count': len(returns),
                'monthly_return_amount': return_amount
            }
            orders.append({'monthly':monthly})
    
            commissions = request.env['sale.commission.achievement.report'].sudo().search([
                ('user_id', '=', salesperson_id),
                ('date', '=', date.today()),
                ('related_res_model', '=', 'account.move')
            ])
            
            invoice_ids = []
            for commission in commissions:
                if commission.related_res_id:
                    invoice_ids.append(commission.related_res_id)

            valid_invoices = request.env['account.move'].sudo().search([
                ('id', 'in', invoice_ids),
                ('move_type', '=', 'out_invoice')
            ])
            valid_invoice_ids = valid_invoices.ids

            commission_invoices = request.env['sale.commission.achievement.report'].sudo().search([
                ('user_id', '=', salesperson_id),
                ('related_res_id', 'in', valid_invoice_ids),
                ('related_res_model', '=', 'account.move')
            ])

            for commission in commission_invoices:
                today_achieved += commission.achieved

            today_achieve_percent = (today_achieved / today_order) * 100

            today_order_count = request.env['sale.order'].sudo().search_count([('user_id', '=',salesperson_id), ('state', '=', 'sale'),('date_order','=',date.today())])

            today = {
                'today_order_target': today_order,
                'today_order_count': today_order_count,
                'today_achieved': round(today_achieved,2),
                'today_pending': round(today_pending,2),
                'today_achieve_percent': round(today_achieve_percent,2),
                'today_invoice_count': today_invoice,
                'today_invoice_amount': today_invoice_amount,
                'today_return_count': today_return,
                'today_return_amount': today_return_amount
            }
            orders.append({'today': today})
            monthly_achievements = {
                'target': target,
                'achievement': achievement
            }
            orders.append({'monthly_achievement': monthly_achievements})

            total_pending = 0
            total_cancelled = 0
            total_pending = 0
            total_achieved = 0
            total_invoice_amount = 0
            total_order = 0
            total_return_amount = 0
            total_target = 0

            total_sales_report = request.env['sale.commission.report'].sudo().search([('user_id','=',salesperson_id)])

            for report in total_sales_report:
                total_achieved += report.achieved
                total_target += report.target_amount
                total_order += report.target_amount / report.date_to.day
                total_order_count = request.env['sale.order'].sudo().search_count([('user_id', '=',salesperson_id), ('state', '=', 'sale')])
                total_cancelled_orders = request.env['sale.order'].sudo().search([('user_id', '=',salesperson_id), ('state', '=', 'cancel')])
                total_pending_orders = request.env['sale.order'].sudo().search([('user_id', '=',salesperson_id), ('state', '!=', 'cancel'),('invoice_status','in',['no','to_invoice'])])
                total_invoices = request.env['account.move'].sudo().search([('user_id', '=',salesperson_id), ('state', '!=', 'cancel')])
                total_returns = request.env['account.move'].sudo().search([('user_id', '=',salesperson_id), ('move_type','=','out_refund'), ('state', '!=', 'cancel')])
            
            for order in total_pending_orders:
                total_pending += order.amount_untaxed
            
            for cancel in total_cancelled_orders:
                total_cancelled += cancel.amount_untaxed

            for invoice in total_invoices:
                total_invoice_amount += invoice.amount_untaxed
            
            for returned in total_returns:
                total_return_amount += returned.amount_untaxed

            total = {
                'total_order_amount': round(total_order,2),
                'total_target': total_target,
                'total_achieved': total_achieved,
                'total_pending': round(total_pending,2),
                'total_cancelled': round(total_cancelled,2),
                'total_order_count': total_order_count, 
                'total_invoice_count': len(total_invoices),
                'total_invoice_amount': total_invoice_amount,
                'total_return_count': len(total_returns),
                'total_return_amount': total_return_amount
            }
            orders.append({'total':total})
            
            return response(
                status=200,
                message="Dashboard Fetched Successfully",
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
        
    @http.route('/api/v1/agent-dashboard-today', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def distributor_dashboard_today(self, **kwargs):
        try:
            salesperson_id = request.env.user.id

            active_plan = request.env['sale.commission.plan'].sudo().search([("date_from", "<", fields.Datetime.now()), ("date_to", ">", fields.Datetime.now())])
            active_plan_ids = active_plan.ids
            sales_commission_report = request.env['sale.commission.report'].sudo().search([("plan_id", "in", active_plan_ids), ('user_id','=',salesperson_id)])

            today_achieved = 0
            today_achieve_percent = 0
            today_products = 0

            months = [report.date_to.month for report in sales_commission_report]

            if date.today().month not in months:
                raise Exception("Please create a commission plan for the target month!")

            for report in sales_commission_report:
                if report.date_to.month == date.today().month:
                    if report.target_amount and report.store_target:
                        completed = round(report.achieved,2)
                        target = round(report.target_amount,2)
                        achievement = round(report.achieved,2)
                        today_order = round(report.target_amount / report.date_to.day,2)
                        break
                    else:
                        raise Exception("Please choose both target amount and store target in your commissions!")     
    
            commissions = request.env['sale.commission.achievement.report'].sudo().search([
                ('user_id', '=', salesperson_id),
                ('date', '=', date.today()),
                ('related_res_model', '=', 'account.move')
            ])
            
            invoice_ids = []
            for commission in commissions:
                if commission.related_res_id:
                    invoice_ids.append(commission.related_res_id)

            valid_invoices = request.env['account.move'].sudo().search([
                ('id', 'in', invoice_ids),
                ('move_type', '=', 'out_invoice')
            ])
            valid_invoice_ids = valid_invoices.ids

            commission_invoices = request.env['sale.commission.achievement.report'].sudo().search([
                ('user_id', '=', salesperson_id),
                ('related_res_id', 'in', valid_invoice_ids),
                ('related_res_model', '=', 'account.move')
            ])

            for commission in commission_invoices:
                today_achieved += commission.achieved

            today_start = datetime.combine(datetime.today(), datetime.min.time())
            today_end = today_start + timedelta(days=1)

            today_orders = request.env['sale.order'].sudo().search([
                ('user_id', '=', salesperson_id),
                ("state", "=", "sale"),
                ('date_order', '>=', today_start),
                ('date_order', '<', today_end),
            ])


            # today_orders = request.env['sale.order'].sudo().search([('user_id', '=',salesperson_id), ('state', '=', 'sale'),('date_order','=',date.today())])

            for order in today_orders:
                for line in order.order_line:
                    today_products += line.product_uom_qty

            today_date = datetime.now()
            today_start = today_date.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_date.replace(hour=23, minute=59, second=59)

            new_customers = request.env['res.partner'].sudo().search_count([('create_date','>=',today_start),('create_date','<=',today_end)])
            
            return response(
                status=200,
                message="Dashboard Fetched Successfully",
                data = {
                    'orders_today': len(today_orders),
                    'products_sold': today_products,
                    'new_customer': new_customers,
                    'target': today_order,
                    'achieved': round(today_achieved,2),
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
        
    @http.route('/api/v1/salesperson-dashboard-today', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value])
    def salesperson_dashboard_today(self, **kwargs):
        try:
            salesperson_id = request.env.user.id

            plans = request.env['distributor.commission.plan'].sudo().search([('state','=','approved'),("date_from", "<=", date.today()), ("date_to", ">", date.today())])

            cases_sold = 0
            store_target = 0
            case_target = 0
            today_products = 0

            for plan in plans:
                for user in plan.user_ids:
                    cases_sold = 0
                    store_target = 0
                    case_target = 0
                    for target in plan.target_ids:
                        if target.date_from <= date.today() <= target.date_to:
                            case_target += round(target.case_target / target.date_to.day,2)
                            lines = request.env['distributor.order.line'].sudo().search([('order_id.user_id','=',user.user_id.id), ('order_id.order_date', '=', date.today()), ('order_id.order_date','<=', date.today())])
                            for line in lines:
                                cases_sold += line.qty
                            store_target += round(target.store_target / target.date_to.day,2)

            today_orders = request.env['distributor.order'].sudo().search([('user_id', '=',salesperson_id), ('order_date','=',date.today())])

            for order in today_orders:
                for line in order.order_line_ids:
                    today_products += line.qty

            today_date = datetime.now()
            today_start = today_date.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_date.replace(hour=23, minute=59, second=59)

            new_customers = request.env['res.partner'].sudo().search_count([('create_date','>=',today_start),('create_date','<=',today_end),('category_id.customer','=',True)])
            today_visited_stores = request.env['res.partner'].sudo().search_count([('is_visited_today','=',True), ('visited_by','=', request.env.user.id)])
            
            return response(
                status=200,
                message="Dashboard Fetched Successfully",
                data = {
                    'orders_today': len(today_orders),
                    'products_sold': today_products,
                    'new_customer': new_customers,
                    'today_store_target': store_target,
                    'today_visited': today_visited_stores,
                    'today_case_target': case_target,
                    'today_sold': cases_sold
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

    @http.route("/api/v1/agent-orders-today", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def dashboard_today_orders(self, **kwargs):
        try:
            today_start = datetime.combine(datetime.today(), datetime.min.time())
            today_end = today_start + timedelta(days=1)

            get_order = GetOrders(**kwargs)

            ORDER_STATUS_MAPPING = {
                'pending': ['draft', 'sent'],
                'completed': ['sale'],
                'cancelled': ['cancel']
            }

            orders = request.env['sale.order'].sudo().search([
                ('user_id', '=', request.env.user.id),
                ('state', 'in', ORDER_STATUS_MAPPING.get(get_order.status)),
                ('date_order', '>=', today_start),
                ('date_order', '<', today_end)
            ], order='date_order desc')

            today_orders = []
            order_count = 0
            products_count = 0
            for order in orders:
                today_orders.append({
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
                order_count += 1
                products_count += len(order.order_line)

            data = {
                "order_count": order_count,
                "products_count": products_count,
                "today_orders": today_orders
            }

            return response(
                status=200,
                message="Today orders Fetch Successfully",
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

    @http.route("/api/v1/dashboard-orders-monthly", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def dashboard_monthly_orders(self, **kwargs):
        try:
            date_to = calendar.monthrange(date.today().year, date.today().month)
            month_start = str(date.today().year) + "-" + str(date.today().month) + "-01"
            month_end = str(date.today().year) + "-" + str(date.today().month) + "-" + str(date_to[1])

            orders = request.env['sale.order'].sudo().search(
                [('user_id', '=', request.env.user.id),
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
                message="Monthly orders Fetch Successfully",
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

    @http.route("/api/v1/today-route-orders", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def daily_route_orders(self, **kwargs):
        try:
            user = request.env.user
            
            routes = request.env['user.route.schedule'].sudo().search([('user_id', '=', user.id), ('date', '=', date.today())])

            if not routes:
                raise Exception("Route Not Set.")
            
            data = []
            total_due = 0
            total_paid = 0

            total_orders = 0
            total_orders_due = 0
            total_orders_paid = 0

            for route in routes:
                for partner_route in route.route_id:
                    for partner in partner_route.partners_ids:
                        partner_id = partner.id
                        orders = request.env['sale.order'].sudo().search(
                            [('partner_id','=', partner_id),
                            ('invoice_status', 'in', ['invoiced','to invoice'])],
                            order='date_order desc'  
                        )
                        paid_orders = orders.filtered(lambda order: order.invoice_ids.payment_state == 'paid')
                        total_orders_paid += len(paid_orders)

                        total_orders += len(orders)

                        for order in orders:
                            invoices = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.payment_state not in ['reversed', 'blocked'] and inv.state=='posted')
                            total_due += sum(invoice.amount_residual for invoice in invoices)
                            total_paid += sum(payment.amount for payment in invoices.matched_payment_ids)

            total_pending = total_due - total_paid

            return response(
                status=200,
                message="Daily Due Fetched Successfully",
                data={ 
                    'due': total_due,
                    'paid': total_paid,
                    'pending': total_pending,
                    'total_orders_count':total_orders,
                    'total_orders_paid_count': total_orders_paid,
                    'total_orders_due_count': total_orders - total_orders_paid,
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
        
    @http.route("/api/v1/new-customers-today", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def new_customers_today(self, **kwargs):
        try:
            today_date = datetime.now()
            today_start = today_date.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_date.replace(hour=23, minute=59, second=59)

            new_customers = request.env['res.partner'].sudo().search([('category_id.customer','=',True),('create_date','>=',today_start),('create_date','<=',today_end)])

            customer_details = []
            customer_count = 0
            for customer in new_customers:
                owner = []
                for child in customer.child_ids:
                    if child.function == "Owner":
                        owner.append({
                            "id": child.id,
                            "name": child.name,
                            "phone": child.phone,
                            "mobile": child.mobile,
                            "address": child.street,
                            "credit_limit": child.credit_limit
                        })

                tags = request.env['res.partner.category'].sudo().search([('mobile_ok','=',True)])
                tag_list = []
                for tag in customer.category_id:
                    if tag in tags:
                        tag_list.append({
                            'id': tag.id,
                            'name': tag.name
                        })
                
                customer_details.append({
                    "id": customer.id,
                    "name": customer.name,
                    "owner": owner,
                    "phone": customer.phone,
                    "mobile": customer.mobile,
                    "address": customer.street,
                    "tags": tag_list,
                    "credit_limit": customer.credit_limit,
                })
                customer_count += 1

            data = {
                "customer_count": customer_count, 
                "customer_details": customer_details
            }

            return response(
                status=200,
                message="New Customers Fetched Successfully",
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
    
    @http.route("/api/v1/salesperson-orders-today", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def salesperson_today_orders(self, **kwargs):
        try:
            history = OrderHistoryDaily(**kwargs)

            ORDER_STATUS_MAPPING = {
                'pending': ['draft', 'pending', 'assigned'],
                'completed': ['completed'],
                'cancelled': ['cancelled']
            }

            orders = request.env['distributor.order'].sudo().search([
                ('user_id', '=', request.env.user.id),
                ('order_date', '=', date.today()),
                ('state', 'in', ORDER_STATUS_MAPPING.get(history.status)) 
            ], order='order_date desc' )

            today_orders = []
            order_count = 0
            products_count = 0
            for order in orders:
                today_orders.append({
                    "id": order.id,
                    "order_number": order.name,
                    "customer": {
                        "id": order.partner_id.id,
                        "name": order.partner_id.name
                    },
                    "order_counts": len(order.order_line_ids),
                    "order_date": order.order_date,
                    "state": order.state,
                    "distributor": order.distributor_id.name
                })
                order_count += 1
                products_count += len(order.order_line_ids)

            data = {
                "order_count": order_count,
                "products_count": products_count,
                "today_orders": today_orders
            }

            return response(
                status=200,
                message="Today orders Fetch Successfully",
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

    @http.route("/api/v1/salesperson-products-today", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_PERSON.value])
    def salesperson_products_today(self, **kwargs):
        try:
            orders = request.env['distributor.order'].sudo().search([
                ('user_id', '=', request.env.user.id),
                ('order_date', '=', date.today()),
            ])

            products = []
            for order in orders:
                for line in order.order_line_ids:
                    matched = [d for d in products if d['id'] == line.product_id.id]
                    if matched:
                        final=matched[0]
                        final['quantity'] = final['quantity'] + line.qty
                        final['orders'].append({
                            'id': order.id,
                            'name': order.name
                        })
                    else:
                        products.append({
                            'id': line.product_id.id,
                            'name': line.product_id.name,
                            'image': line.product_id.image_1920,
                            'price': line.product_id.list_price,
                            'quantity': line.qty,
                            'orders': [{
                                'id': order.id,
                                'name': order.name
                            }] 
                        })

            data = {
                "products_count": len(products),
                "product_details": products
            }

            return response(
                status=200,
                message="Today orders Fetch Successfully",
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
        
        
    @http.route("/api/v1/salesperson-list", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def salesperson_list(self, **kwargs):
        try:
            team = request.env['crm.team'].sudo().search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            url = request.env['ir.config_parameter'].sudo().\
                get_param('web.base.url')

            if not team: 
                raise Exception("No team found under the user!!")

            data = []

            for member in team.crm_team_member_ids:
                data.append({
                    'id': member.id,
                    'name': member.name,
                    'email': member.user_id.login,
                    'phone': member.user_id.phone,
                    'mobile': member.user_id.mobile,
                    'image': f"{url}/web/image/res.users/{member.id}/avatar_128"
                })

            return response(
                status=200,
                message="Salespeople fetched successfully!!",
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
        
    @http.route("/api/v1/agent-products-today", type="json", auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def agent_products_today(self, **kwargs):
        try:
            today_start = datetime.combine(datetime.today(), datetime.min.time())
            today_end = today_start + timedelta(days=1)

            orders = request.env['sale.order'].sudo().search([
                ('user_id', '=', request.env.user.id),
                ("state", "=", "sale"),
                ('date_order', '>=', today_start),
                ('date_order', '<', today_end),
            ])

            products = []
            for order in orders:
                for line in order.order_line:
                    matched = [d for d in products if d['id'] == line.product_id.id]
                    if matched:
                        final=matched[0]
                        final['quantity'] = final['quantity'] + line.product_uom_qty
                        final['orders'].append({
                            'id': order.id,
                            'name': order.name
                        })
                    else:
                        products.append({
                            'id': line.product_id.id,
                            'name': line.product_id.name,
                            'image': line.product_id.image_1920,
                            'price': line.product_id.list_price,
                            'quantity': line.product_uom_qty,
                            'orders': [{
                                'id': order.id,
                                'name': order.name
                            }] 
                        })

            data = {
                "products_count": len(products),
                "product_details": products
            }

            return response(
                status=200,
                message="Today orders Fetch Successfully",
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