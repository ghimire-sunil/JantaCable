# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response

from functools import wraps
from .utils import ALLOWED_URL, response, required_login, formate_error
from .schema.user import ChangePassword ,UserProfile
from pydantic import ValidationError
from odoo.exceptions import UserError
import base64
import json

class UserController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner
    
    @http.route('/api/v1/user', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def user(self, **kwargs):       
        try:
            user = kwargs.get('user')

            return response(
                status=200,
                message="User Fetch Successfully",
                data={
                    "id": user.id,
                    "name": user.name,
                    "email": user.login,
                    "address": user.partner_id.contact_address_complete,
                    "phone": user.partner_id.phone,
                    "mobile": user.partner_id.mobile,
                    "image": user.image_1920,
                    "latitude": user.partner_id.partner_latitude,
                    "longitude": user.partner_id.partner_longitude,
                    "role": user.role
                }
            )
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
    
    @http.route('/api/v1/change-password', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def change_password(self, **kwargs):
        try:    
            change_password = ChangePassword(**kwargs)
            user = change_password.user 
            
            db_name = request.env.cr.dbname
            user_id = request.session.authenticate(
                dbname=db_name,
                credential={
                    'login': user.login,
                    'password': change_password.old_password,
                    'type': 'password'
                }
            )       
            
            if user_id:
                user.password = change_password.password
                user._set_new_password()

            return response(
                status=200,
                message="Password Updated Successfully",
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
            msg = e.args[0]
            if e.args[0] == "Access Denied":
                msg = "The old password entered is incorrect. Please verify and try again."
            return response(
                status=400,     
                message=msg,
                data=None
            )
            
    
    @http.route('/api/v1/update-profile', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def update_password(self, **kwargs):
        try:   
            profile = UserProfile(**kwargs)
            user= profile.user
            
            user.sudo().write({
                "login": profile.email,
                "name": profile.name,
            })      
            
            user.partner_id.sudo().write({
                "phone": profile.phone,
                "street": profile.address
            })      

            return response(
                status=200,
                message="User Profile Updated Successfully",
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

    @http.route('/api/v1/user/image', type='http', methods=['POST'], auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @make_response
    def update_image(self, **kwargs):
        
        try:
            user = request.env.user
            image = kwargs.get('image')

            if image is None:
                return {
                'status':400,
                'message':'Missing fields !!'
                }

            image_base64 = base64.b64encode(image.read())

            user.sudo().write({
                'image_1920':image_base64
            })
            

            return  {
                'data':{ 
                    "status":200,
                    "data":None,
                    "message":'Image updated successfully!!'
                }
            }

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
