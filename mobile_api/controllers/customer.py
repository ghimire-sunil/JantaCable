# -*- coding: utf-8 -*-

import uuid
from odoo import http, SUPERUSER_ID
from odoo.http import request, Response
from odoo.exceptions import UserError

from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from .schema.customer import Contact
from pydantic import ValidationError
import base64
import json

class CustomerController(http.Controller):     

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner
    
    @http.route('/api/v1/province-list', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    def province_list(self):
        try:
            provinces = request.env['res.country.state'].sudo().search([('country_id', '=', request.env.company.country_id.id)])
            province_list = []
            for province in provinces:
                province_list.append({
                    'id': province.id,
                    'name': province.name
                })
            return response(
                status=200,
                message="Provinces fetched successfully!!",
                data=province_list
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
        
        
    @http.route('/api/v1/outlet-types', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    def outlet_types(self):
        try:
            outlets = request.env['outlet.type'].sudo().search([])
            outlet_list = []
            for outlet in outlets:
                outlet_list.append({
                    'id': outlet.id,
                    'name': outlet.name
                })
            return response(
                status=200,
                message="Outlets fetched successfully!!",
                data=outlet_list
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


    @http.route('/api/v1/create-store', type='http', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @make_response
    @check_role([UserRole.SALE_PERSON.value])
    def create_contact(self, **kwargs):
        try:
            contact = Contact(**kwargs)
            image = contact.image
            image_base64 = base64.b64encode(image.read())
            artwork_image_base64 = False

            province = request.env['res.country.state'].sudo().search([('name','ilike',contact.province)])

            if not province:
                raise Exception("Province not found. Please check the spelling!!")
            
            customer_tag = request.env['res.partner.category'].sudo().search([('customer','=',True)])

            store = request.env['res.partner'].sudo().create({
                "name": contact.name,
                "street": contact.street,
                "street2": contact.street2,
                "city": contact.city,
                "state_id": province.id,
                "company_type": "company",
                "phone": contact.phone,
                "credit_limit": float(contact.credit_limit_value),
                "credit_limit_span": int(contact.credit_limit_days),
                "outlet_type": int(contact.outlet_type),
                "vat": contact.pan_no,
                "is_company": True, 
                "email": contact.email,    
                "registration_number": contact.registration_number,
                "dealer_reference": contact.dealer_reference,
                "image_1920": image_base64,
                "category_id": [(4, customer_tag.id)] if customer_tag else False,
                "private_label": contact.private_label
                
            })

            if contact.artwork_reference:
                artwork = contact.artwork_reference
                artwork_image_base64 = base64.b64encode(artwork.read())

            if store.private_label:
                store.write({
                    "artwork_reference": artwork_image_base64,
                    "lead_time_note": contact.lead_time_note,
                    "min_order_qty_check": contact.min_order_qty_check,
                    "packaging_notes": contact.packaging_notes,
                })

            location = json.loads(contact.location)
            if location['latitude'] > 90 or location['latitude'] < -90 or location['longitude'] > 180 or location['longitude'] < -180:
                raise UserError("Latitude must be between 90 and -90. Longitude must be between -180 and 180")
            store.partner_latitude = location['latitude']
            store.partner_longitude = location['longitude']

            if contact.secondary_contact_name or contact.secondary_contact_phone:
                child = request.env['res.partner'].sudo().create({
                    "name": contact.secondary_contact_name,
                    "phone": contact.secondary_contact_phone,
                    "email": contact.secondary_contact_email,
                    "type": "contact"
                })
                store.child_ids = [(4,child.id)]

            return  {
                'data':{ 
                    "status":200,
                    "data":None,
                    "message":'Store created successfully!!'
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


    @http.route('/api/v1/address', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def my_address(self, **kw):
        try:
            partner_id= request.env['res.users'].with_user(SUPERUSER_ID).browse(request.env.user.id).partner_id
            primary = partner_id.read(['name','street','street2','city','country_id','contact_address_complete','type','phone','partner_latitude','partner_longitude'])
        
            addresses = partner_id.child_ids.read(['name','street','street2','city','country_id','contact_address_complete','type','phone','partner_latitude','partner_longitude'])            
            primary.extend(addresses)
            return response(
                status=200,
                message="Address fetched successfully!!",
                data=primary
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

    @http.route('/api/v1/address/create', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def create_address(self, **kw):
        try:
            name = kw.get('name')
            street=kw.get('street')
            phone=kw.get('phone')

            if name is None or street is None or phone is None:
                raise Exception('Missing fields!')

            partner_id= request.env['res.users'].sudo().browse(request.env.user.id).partner_id
            
            new_address = request.env['res.partner'].sudo().create({
                'name':name,
                'street':street,
                'street2': kw.get('street2') or None,
                'city': kw.get('city') or None,
                'phone':phone,
                'parent_id':partner_id.id,
                'type':'delivery',
                'partner_latitude':kw.get('lat') or 0,
                'partner_longitude':kw.get('long') or 0,
            })
            return response(
                status=200,
                message="Address created successfully!!",
                data=new_address.read(['name','street','street2','city','type'])[0]
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

    @http.route('/api/v1/address/update', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def update_address(self, **kw):
        try:
            id_ = kw.get('child_id')
            name = kw.get('name')
            street=kw.get('street')
            phone=kw.get('phone')

            if id_ is None or  name is None or street is None or phone is None :
                raise Exception("Missing Fields !!")

            parent_id= request.env['res.users'].sudo().browse(request.env.user.id).partner_id.id
            child_id = request.env['res.partner'].with_user(SUPERUSER_ID).search([('id','=',id_)],limit=1)

            if not child_id:
                raise Exception("Address Not Found!!")

            if child_id.parent_id.id != parent_id:
                raise Exception("You are not allowed to delete this address !!")

            child_id.write({
                'name':name,
                'street':street,
                'street2': kw.get('street2') or None,
                'city': kw.get('city') or None,
                'phone':phone,
                'partner_latitude':kw.get('lat') or 0,
                'partner_longitude':kw.get('long') or 0,
            })
            return response(
                status=200,
                message="Address updated successfully!!",
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
            

    @http.route('/api/v1/address/delete', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def delete_address(self, **kw):
        try:
            id_ = kw.get('child_id')

            if id_ is None :
                raise Exception("Missing Fields !!")

            parent_id= request.env['res.users'].sudo().browse(request.env.user.id).partner_id.id
            child_id = request.env['res.partner'].sudo().search([('id','=',id_)],limit=1)

            if not child_id:
                raise Exception("Address Not Found!!")

            if child_id.parent_id.id != parent_id:
                raise Exception("You are not allowed to delete this address !!")

            child_id.unlink()
            return response(
                status=200,
                message="Address Deleted successfully!!",
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