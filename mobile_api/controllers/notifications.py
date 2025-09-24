from odoo import SUPERUSER_ID, http
from odoo.http import request, Response
from pydantic import ValidationError
from .utils import response, required_login, formate_error, check_role, UserRole
from datetime import date, datetime, timedelta
import json
import base64

class NotificationController(http.Controller):

    @http.route("/api/v1/register/token", type="json", csrf=False, auth="public")
    @required_login
    def registerToken(self, **kw):
        try:
            user = request.env.user

            user = request.env["res.users"].sudo().browse(user.id)
            token = kw.get("deviceToken")
            origin = kw.get("origin")

            if not token:
                raise Exception("Device Token Compulsory !!")
            if not origin:
                raise Exception("Origin App Compulsory!!")

            expo_device = (
                request.env["expo.device"]
                .with_user(SUPERUSER_ID)
                .search(
                    [("user_id", "=", user.id),
                     ("origin_app", "=", origin)],
                    limit=1,
                )
            )

            if expo_device:
                expo_device.expo_push_token = token
            else:
                request.env["expo.device"].with_user(SUPERUSER_ID).create(
                    {
                        "user_id": user.id,
                        "expo_push_token": token,
                        "origin_app": origin
                    }
                )

            return response(
                    status=200,
                    message="Device Token Registered!!",
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
    

    @http.route("/api/v1/remove/token", type="json", csrf=False, auth="public")
    @required_login
    def removeToken(self, **kw):
        try:
            origin = kw.get("origin")
 
            user = request.env.user

            if not origin:
                raise Exception("Origin App Compulsory!!")

            user = request.env["res.users"].sudo().browse(user.id)

            expo_device = (
                request.env["expo.device"]
                .with_user(SUPERUSER_ID)
                .search([("user_id", "=", user.id), ("origin_app", "=", origin)])
            )

            if expo_device:
                expo_device.unlink()
        
            return response(
                    status=200,
                    message="Device Token Removed!!",
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

    @http.route('/api/v1/notifications', type='json', auth='public', csrf=False)
    @required_login
    def notifications(self, **kwargs):
        try:
            user_id = request.env.user.id
            origin = kwargs['origin']

            read_messages = []
            unread_messages = []
            expo_device = request.env["expo.device"].search(
                [("user_id", "=", user_id), ("origin_app","=",origin)],
                limit = 1
            )

            if expo_device:
                messages = request.env['expo.message'].sudo().search([('user_id','=',user_id), ('date', '<=', datetime.now())], order="date desc")
                for message in messages:
                    date_message = message.date + timedelta(hours=5, minutes=45)
                    if message.read_message:
                        read_messages.append({
                            'id': message.id,
                            'title': message.title,
                            'body': message.body,
                            'date': date_message.date(),
                            'time': date_message.time(),
                            'read_status': message.read_message
                        })
                    else:
                        unread_messages.append({
                            'id': message.id,
                            'title': message.title,
                            'body': message.body,
                            'date': date_message.date(),
                            'time': date_message.time(),
                            'read_status': message.read_message
                        })

            data = {
                'unread_messages_num': len(unread_messages),
                'read_messages': read_messages,
                'unread_messages': unread_messages 
            }

            return response(
                status=200,
                message="Notifications listed successfully!",
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
        
    @http.route('/api/v1/set-notif-read', type='json', auth='public', csrf=False)
    @required_login
    def set_notif_read(self, **kwargs):
        try:
            user_id = request.env.user.id
            message = kwargs['message_id']
            origin = kwargs["origin"]

            expo_device = request.env["expo.device"].search(
                [("user_id", "=", user_id), ("origin_app","=",origin)],
                limit = 1
            )

            if expo_device:
                message = request.env['expo.message'].sudo().search([('id','=',message), ('user_id','=',user_id), ('date', '<=', datetime.now())], order="date desc")
                message.read_message = True

            return response(
                status=200,
                message="Message Read Successfully!",
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
        
    @http.route('/api/v1/unread-notifications', type='json', auth='public', csrf=False)
    @required_login
    def unread_notifications(self, **kwargs):
        try:
            user_id = request.env.user.id
            origin = kwargs["origin"]

            unread_messages = 0
            expo_device = request.env["expo.device"].search(
                [("user_id", "=", user_id), ("origin_app","=",origin)],
                limit = 1
            )

            if expo_device:
                messages = request.env['expo.message'].sudo().search([('user_id','=',user_id), ('date', '<=', datetime.now())], order="date desc")
                for message in messages:
                    if not message.read_message:
                        unread_messages += 1
                    

            data = {
                'unread_messages_num': unread_messages
            }

            return response(
                status=200,
                message="Unread notifications counted successfully!",
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

    @http.route('/api/v1/mark-all-read', type='json', auth='public', csrf=False)
    @required_login
    def mark_all_read(self, **kwargs):
        try:
            user_id = request.env.user.id
            origin = kwargs["origin"]

            expo_device = request.env["expo.device"].search(
                [("user_id", "=", user_id), ("origin_app","=",origin)],
                limit = 1
            )

            if expo_device:
                messages = request.env['expo.message'].sudo().search([('user_id','=',user_id), ('date', '<=', datetime.now())], order="date desc")
                for message in messages:
                    if not message.read_message:
                        message.read_message = True
                
            return response(
                status=200,
                message="Marked all messages as read successfully!",
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