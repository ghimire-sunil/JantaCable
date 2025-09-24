# -*- coding: utf-8 -*-

import uuid
from odoo import http
from odoo.http import request, Response
from datetime import date
import math

from .utils import ALLOWED_URL, response, required_login, formate_error
from .schema.route import Route, RouteCustomer, Contact, EditContact
from pydantic import ValidationError

import base64
import json

class RouteController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/routes', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def routes(self, **kwargs):
        try:
            route = Route(**kwargs)
            user = route.user
            limit = route.limit or 10
            page = route.page or 1
            offset = (page - 1) * limit

            search_query = route.search_query
            search_field = route.search_field
            if search_query and isinstance(search_query, str):
                search_query = search_query.strip().lower()

            # SEARCH
            SEARCH_MAPPING = {
                'name': 'name',
                'phone': 'phone',
                'PAN': 'vat',
                'code': 'dealer_reference',
                'address': 'contact_address_complete'
            }

            if route.search_field:
                search_field = SEARCH_MAPPING.get(route.search_field)

            if route.schedule_type == 'today':
                filter_domain = ('date', '=', date.today())
            else:
                filter_domain = ('date', '>=', date.today())
            
            routes = request.env['user.route.schedule'].sudo().search(
                domain=[
                    filter_domain,
                    ('user_id', '=', user.id)
                ]
            )

            data = []
            for rt in routes:

                customers = []
                
                search_domain = [('route_id', '=', rt.route_id.id),("category_id.customer", "=", True)]

                if search_query:
                    if search_field:
                        if search_field == 'phone':
                            search_domain = [
                                ('route_id', '=', rt.route_id.id),
                                ("category_id.customer", "=", True),
                                '|',
                                ('phone', 'ilike', search_query),
                                ('mobile', 'ilike', search_query)]
                        else:
                            search_domain = [('route_id', '=', rt.route_id.id), (search_field, 'ilike', search_query)]
                    else:
                        search_domain = [
                            ('route_id', '=', rt.route_id.id),
                            ("category_id.customer", "=", True),
                            '|','|','|','|','|',
                            ('name', 'ilike', search_query),
                            ('phone', 'ilike', search_query),
                            ('mobile', 'ilike', search_query),
                            ('vat', 'ilike', search_query),
                            ('dealer_reference', 'ilike', search_query),
                            ('contact_address_complete', 'ilike', search_query)
                        ]

                #FILTER
                if route.filter_field:

                    if not route.category_filter and not route.credit_filter and not route.private_label_filter:
                        raise Exception("You need to specify the filter you want!!")

                    if "category" in route.filter_field:
                        if route.category_filter:
                            search_domain += [('outlet_type.name', 'in', route.category_filter)]

                    if "credit_limit" in route.filter_field:       
                        if route.credit_filter:
                            if 'ok' in route.credit_filter and 'overdue' in route.credit_filter:
                                search_domain += ['|', ('credit','<=', 0), ('credit', '>', 0)]
                            else:
                                if 'ok' in route.credit_filter:
                                    search_domain += [('credit','<=', 0)]
                                if 'overdue' in route.credit_filter:
                                    search_domain += [('credit', '>', 0)]

                    if "private_label" in route.filter_field: 
                        if route.private_label_filter:
                            if 'enabled' in route.private_label_filter and 'disabled' in route.private_label_filter:
                                search_domain += ['|', ('private_label','=', True), ('private_label','=',False)]
                            else:
                                if 'enabled' in route.private_label_filter:
                                    search_domain += [('private_label','=', True)]
                                if 'disabled' in route.private_label_filter:
                                    search_domain += [('private_label','=',False)]

                partners = request.env['res.partner'].sudo().search(domain=search_domain, limit=limit, offset=offset)
                
                for partner in partners:
                    tags = request.env['res.partner.category'].sudo().search([('mobile_ok','=',True)])

                    tag_list = []
                    for tag in partner.category_id:
                        if tag in tags:
                            tag_list.append({
                                'id': tag.id,
                                'name': tag.name
                            })

                    credit_summary = {
                        'credit_limit': partner.credit_limit,
                        'credit_used': partner.credit,
                        'credit_days': partner.credit_limit_span,
                        'credit_limit_exceeded': True if partner.credit > partner.credit_limit else False,
                        'credit_days_exceeded': partner.credit_limit_span_exceeded
                    }

                    customers.append({
                        "id": partner.id,
                        "name": partner.name,
                        "category": partner.outlet_type.name,
                        "address": partner.contact_address_complete,
                        "phone": partner.phone,
                        "mobile": partner.mobile,
                        "pan_no": partner.vat,
                        "dealer_reference_code": partner.dealer_reference,
                        "tags": tag_list,
                        "latitude": partner.partner_latitude,
                        "longitude": partner.partner_longitude,
                        "credit_summary": credit_summary,
                        "is_ordered_today": partner.is_ordered_today,
                        "is_visited_today": partner.is_visited_today,
                        "is_payment_taken_today": partner.is_payment_taken_today
                    })

                data.append({       
                    "id": rt.route_id.id,
                    "key": uuid.uuid4(),
                    "name": rt.route_id.name,
                    "code": rt.route_id.code,
                    "date": rt.date.strftime("%Y-%m-%d"),
                    "partner_count": rt.route_id.partner_counts,
                    "customers": customers
                })

            return response(
                status=200,
                message="Route Fetched Successfully",
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

    @http.route('/api/v1/route-contact', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    # @required_login
    def contact_routes(self, **kwargs):
        try:
            route_customer = RouteCustomer(**kwargs)
            user = route_customer.user

            page = route_customer.page or 1
            limit = route_customer.limit or 10
            offset = (page - 1) * limit

            search_query = route_customer.search_query

            domain = [('route_id', '=', route_customer.route_id),("category_id.customer", "=", True)]

            if search_query and isinstance(search_query, str):
                search_query = search_query.strip().lower()
                domain.append(('name', 'ilike', search_query))

            partners = request.env['res.partner'].sudo().search(domain, offset=offset, limit=limit)
            
            total_count = request.env['res.partner'].sudo().search_count(domain)
            data = []
            for partner in partners:
                data.append({
                    "id": partner.id,
                    "name": partner.name,
                    "address": partner.street,
                    "email": partner.email,
                    "phone": partner.phone,
                    "mobile": partner.mobile,
                    "latitude": partner.partner_latitude,
                    "longitude": partner.partner_longitude,
                    "is_ordered_today": partner.is_ordered_today,
                    "is_visited_today": partner.is_visited_today,
                    "is_payment_taken_today": partner.is_payment_taken_today
                })

            return response(
                status=200,
                message="Route Customer Successfully",
                data={
                    "current_page":page,
                    "total_page":  math.ceil(total_count/limit),
                    'data':data,
                    'search_query':search_query
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

    @http.route('/api/v1/contact', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def contact(self, **kwargs):
        try:    
            contact = Contact(**kwargs)

            partner = request.env['res.partner'].sudo().search([
                ('id', '=', contact.contact_id)
            ], limit=1)

            if not partner:
                raise Exception("Customer Not Found")

            return response(
                status=200,
                message="Route Customer Successfully",
                data={
                    "id": partner.id,
                    "name": partner.name,
                    "address": partner.contact_address_complete,
                    "email": partner.email,
                    "phone": partner.phone,
                    "mobile": partner.mobile,
                    "latitude": partner.partner_latitude,
                    "longitude": partner.partner_longitude,
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

    @http.route('/api/v1/edit-contact', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def edit_contact(self, **kwargs):
        try:    
            contact = EditContact(**kwargs)

            partner = request.env['res.partner'].sudo().search([
                ('id', '=', contact.contact_id)
            ], limit=1)

            if not partner:
                raise Exception("Customer Not Found")

            partner.write({
                'partner_latitude': contact.latitude,
                'partner_longitude': contact.longitude,
                'street': contact.street,
                'street2': contact.street2,
                'city': contact.city
            })

            return response(
                status=200,
                message="Customer Updated Successfully",
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
    
    @http.route('/api/v1/update-contact', type='http', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @make_response
    def update_contact(self, **kwargs): 
        try:
            contact = EditContact(**kwargs)
            
            partner = request.env['res.partner'].sudo().search([
                ('id', '=', contact.contact_id)
            ], limit=1)

            if not partner:
                raise Exception("Customer Not Found")
            
            if contact.owner:
                owners = json.loads(contact.owner)

                for owner in owners:
                    owner_detail = request.env['res.partner'].sudo().search([('id','=',owner['id']), ('function','=','Owner')])
                    if not owner_detail:
                        raise Exception("No owner found for this record!!")
                    
                    if owner_detail.parent_id.id != partner.id:
                        raise Exception("You are not allowed to edit this record!!")
                    
                    owner_detail.write({
                        "name": owner['name'],
                        "phone": owner['phone']
                    })

            image = contact.image
            image_base64 = base64.b64encode(image.read())

            province_detail = request.env['res.country.state'].sudo().search([('name','ilike',contact.province)])
            if not province_detail:
                raise Exception("No province found for this name!!")
            
            partner.write({
                'name': contact.name,
                'phone': contact.phone,
                'partner_latitude': float(contact.latitude),
                'partner_longitude': float(contact.longitude),
                'street': contact.street,
                'street2': contact.street2,
                'city': contact.city,
                'state_id': province_detail.id,
                'email': contact.email,
                'vat': contact.pan_no,
                'dealer_reference': contact.dealer_reference,
                'image_1920': image_base64
            })

            return  {
                'data':{ 
                    "status":200,
                    "data":None,
                    "message":'Store updated successfully!!'
                }
            }

        except ValidationError as error:
            return  {
                'data':{ 
                    "status":400,
                    "data":formate_error(error.errors()),
                    "message":'Data Validation Error!!'
                }
            }
        
        except Exception as e:   
            return  {
                'data':{ 
                    "status":400,
                    "data":None,
                    "message":e.args[0]
                }
            }

    @http.route('/api/v1/update-visit-status', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def update_visited_status(self, **kwargs): 
        try:
            customer_id = kwargs['customer_id']

            partner = request.env['res.partner'].sudo().search([('id','=',customer_id)])
            
            if not partner:
                raise Exception("Customer Not Found")

            partner.is_visited_today = True
            partner.visited_by = request.env.user.id

            return response(
                status=200,
                message="Customer Updated Successfully",
                data=None
            )

        except ValidationError as error:
            return response(
            status=400,
            message="Data Validation Error",
            data=formate_error(error.errors(
                include_url=False,
                include_input=False
            ))
        )
        except Exception as e:
            return response(
            status=400,
            message=e.args[0],
            data=None
        )