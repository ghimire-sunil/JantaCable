# -*- coding: utf-8 -*-
import jwt
import re

from odoo import http
from odoo.http import request

from .utils import ALLOWED_URL, response, SECRET_KEY, formate_error
from .schema.auth import Login,ForgetPassword
from pydantic import ValidationError

from datetime import datetime, timezone, timedelta

class AuthController(http.Controller):
    @http.route('/api/v1/login', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    def login(self, **kwargs):
        try:                        
            login = Login(**kwargs)         
            db_name = request.env.cr.dbname
            
            user_id = request.session.authenticate(
                dbname=db_name,
                credential={
                    'login': login.email,
                    'password': login.password, 
                    'type': 'password'
                }
            )   

            user = request.env['res.users'].sudo().browse(user_id.get('uid'))
            
            token = jwt.encode({
                'id': user.id,
                'login': user.login,
                "name": user.name,
                "exp": datetime.now(tz=timezone.utc) + timedelta(days=7)    
            }, SECRET_KEY, algorithm='HS256')

            return response(status=200, message='Login Successfully', data={        
                "user": {
                    "id": user.id,
                    "name": user.name,  
                    "email": user.email,
                    "image_1920": user.image_1920,
                    "role": user.role
                },      
                "token": token      
            })
        except ValidationError as error:
            return response(        
                status=400,
                message="Data Validation Error",      
                data=formate_error(error.errors(
                    include_url=False,
                ))
            )   
        except Exception as e:
            if e.args[0] == 'Access Denied':
                error = "Invalid credentials"
            else:
                error = e.args[0]
            return response(
                status=400,     
                message=error, 
                data=None
            )
            
    @http.route('/api/v1/forget-password', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    def forget_password(self, **kwargs):
        try:
            forget_password = ForgetPassword(**kwargs)
            
            request.env['res.users'].sudo().reset_password(
                forget_password.email
            )
            
            return response(
                status=200,
                message="Password reset instructions sent to your email",
            )
        except ValidationError as error:
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors(
                    include_url=False
                ))
            )
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        
    @http.route('/api/v1/signup', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    def customer_signup(self,**kwargs):
        try:

            fields = ['email', 'name', 'password']

            if not all(field in kwargs for field in fields):
                raise ValueError("Please supply all required fields!")
        
            for key, value in kwargs.items():
                if not kwargs[key]:
                    raise ValueError("Please supply all required fields!")
                
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', kwargs['email']):
                raise ValueError(
                    "Please provide a valid email!")
                
            password = kwargs['password']

            if not re.search(r"[A-Z]", password):
                raise ValueError(
                    "Password must contain at least one uppercase letter")
            if not re.search(r"\d", password):
                raise ValueError("Password must contain at least one number")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                raise ValueError(
                    "Password must contain at least one special character")
            
            new_user = request.env['res.users'].sudo().create({
                'name': kwargs['name'],
                'login': kwargs['email'],
                'password': kwargs['password'],
                'role': 'customer',
                'sel_groups_1_10_11': 11,
            })

            new_user.phone = kwargs['phone']

            token = jwt.encode({
                'id': new_user.id,
                'login': new_user.login,
                "name": new_user.name,
                "exp": datetime.now(tz=timezone.utc) + timedelta(days=7)    
            }, SECRET_KEY, algorithm='HS256')
            
            return response(
                status=200,
                message="Customer created successfully!",
                data={        
                "user": {
                    "id": new_user.id,
                    "name": new_user.name,  
                    "email": new_user.login,
                    "role": new_user.role,
                    "image_1920": new_user.image_1920
                },      
                "token": token 
            })
        
        except ValueError as error: 
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
