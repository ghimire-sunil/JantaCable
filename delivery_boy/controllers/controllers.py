# -*- coding: utf-8 -*-
from os import name
from odoo import http,Command,SUPERUSER_ID
from odoo.http import request,Response
from functools import wraps
import json
from odoo.addons.payment.controllers.portal import PaymentPortal
import jwt
import logging
from . import constant
from datetime import datetime,time
import base64

import psycopg2
_logger = logging.getLogger(__name__)


# response format
"""
 {  jsonrpc :2.0
    result:{
      status:200,
      message::"something went wrong",
      data :any
    }
 }

"""

def make_response(func):
    def inner(*args,**kwargs):
        result = func(*args,**kwargs)
        headers = {"Access-Control-Allow-Origin": "*"}
        return Response(json.dumps({
            'result':result
        }),headers=headers, content_type='application/json', status=200)  

    return inner

def endoceJwt(token,secret_key):
    user=None
    try:
     user = jwt.decode(token,secret_key,algorithms='HS256')
    except Exception as e:
        print(e)
    return user


class DeliveryBoy(http.Controller):

    @http.route('/delivery/api/login',type='json', auth='public',csrf=False,methods=['POST'])
    def login(self, **kw):
        email = kw.get('email')
        password=kw.get('password')

        if email is None or password is None:
            return {
            'status':400,
            'message':'Missing fields',
            'data':None
            }

        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 

        try:
         userId = request.session.authenticate(request.env.cr.dbname,{
             'login':email,
             'password':password,
             'type':'password'
         })
        except :
             return {
            'status':400,
            'message':'Email or Password Incorrect !!',
            'data':None
            }

        if not userId :
            return {
            'status':403,
            'message':'access denied',
            'data':None
            }


        
        user = request.env['res.users'].sudo().browse(userId['uid'])

        if not user.is_delivery_person :
            return {
            'status':403,
            'message':'access denied',
            'data':None
            }

        user = user.read(['login','name','phone','street','is_delivery_person','image_128'])[0]
        token = jwt.encode({
            'id':user['id'],
            'login':user['login'],
            'phone':user['phone']
        },secret_key,algorithm='HS256')    

        if user['image_128']:
            user['image_128'] =  user['image_128'].decode('utf-8')

        return {
            'status':201,
            'message':"Login SuccessFully !!",
            'data': {
            'user':user,
            'token':token
        }}
    
       
    @http.route('/delivery/api/resetpassword',type="json",methods=['POST'],csrf=False, auth='public')
    def resetpassword(self, **kw):
        email=kw.get('email')
        # print(email)
        if email is None:
            return {
                'status':400,
                'message':'Missing email',
                'data':None
            }
        try:
         request.env['res.users'].sudo().reset_password(email)
        except Exception as e:
            return {
                'status':500,
                'message':'Email may not found!! Try again',
                'data':None
            }

        return {
            'status':201,
            'message':'Password reset sent instructions to the email',
            'data':None
        }

    @http.route('/delivery/api/changepassword',type="json",methods=['POST'],csrf=False, auth='public')
    def changepassword(self, **kw):
        old_password=kw.get('oldPassword')
        new_password=kw.get('newPassword')
        # print(email)
        token = request.httprequest.headers.get('Authorization')

        db_name =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.db_name',constant.db_name) 
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 

        if not token:
             return {
                'status':403,
                "message":"Token Missing",
                'data':None
            }

        user = endoceJwt(token.split(' ')[1],secret_key)
     
        if not user:
            return {
                'status':401,
                "message":"Token Expired !!",
                'data':None
            }
        try:
         userId = request.session.authenticate(request.env.cr.dbname,{
             'login':user['login'],
             'password':old_password,
             'type':'password'
         })
        except :
             return {
            'status':403,
            'message':'Old Password Incorrect !!',
            'data':None
            }

        try:
            user = request.env['res.users'].sudo().browse(userId)
            user.password=new_password
            user._set_new_password()
        except Exception as e:
            return {
                'status':500,
                'message':'Something went wrong in server',
                'data':None
            }

        return {
            'status':201,
            'message':'New Password is set',
            'data':None
        }
        

    @http.route('/delivery/api/user',type='json',methods=['POST'],csrf=False, auth='public')
    def getUser(self, **kw):
        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }
        user = request.env['res.users'].sudo().browse(user['id'])

        if not user.is_delivery_person:
            return {
                    'status':403,
                    "data":None,
                    'message':"Forbidden"
            }

        user_data = user.read(['name','login','phone','street','image_128'])[0]
        
        return {
                'status':200,
                'message':"success",
                "data":{
                    'user':user_data
                    }
            }

    @http.route('/delivery/api/user/update',type='json',methods=['POST'],csrf=False, auth='public')
    def updateprofile(self, **kw):
       
        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                "message":"Token Missing"
            }

        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
     
        if not user:
            return {
                'status':401,
                "message":"Token Expired !!"
            }

        name = kw.get('name')
        email = kw.get('email')
        phone=kw.get('phone')
        address=kw.get('address')
        
        payload={}

        if name :
            payload['name']=name
        if email :
            payload['login']=email
            payload['email']=email
        if phone :
            payload['phone']=phone
        if address :
            payload['street']=address

        if email and user['login'] != email:
            is_exist= request.env['res.users'].sudo().search([('login','=',email)],limit=1)
            if  is_exist:
                return {
                        'status':400,
                        'message':'Email used by another user!!'
                        }

        try :
          user = request.env['res.users'].with_user(SUPERUSER_ID).browse(user['id'])
          user.write(payload)

        except Exception as e:
            return {
                "status":500,
                "data":None,
                "message":'Something went wrong !!'
            }
        
        return {
                "status":201,
                "data":None,
                "message":'Updated value!!'
            }
    
    @http.route('/delivery/api/user/image',type='http',methods=['POST'],csrf=False, auth='public')
    @make_response
    def updateImage(self, **kw):
       
        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'data':{
                'status':401,
                "message":"Token Missing"
               }
             }

        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
     
        if not user:
            return {
                'data':{
                'status':401,
                "message":"Token Expired !!"
            }}

        image = kw.get('image')
        print(image)
        if image is None:
            return {
            'status':400,
            'message':'Missing fields !!'
            }

        image_base64 = base64.b64encode(image.read())
        
        try :
          user = request.env['res.users'].with_user(SUPERUSER_ID).browse(user['id'])
          user.write({
            'image_1920':image_base64
          })
        except Exception as e:
            return {
                'data':{
                "status":500,
                "data":None,
                "message":'Something went wrong !!'
            }}
        
        return  {
                'data':{ 
                "status":201,
                "data":None,
                "message":'Profile Picture Changed!!'
            }}
    

    @http.route('/delivery/api/picking',type='json',csrf=False, auth='public')
    def getPicking(self,**kw):
        token = request.httprequest.headers.get('Authorization')

        
        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }
        state = kw.get('state')
        date = kw.get('date')
        page = kw.get('page') or 1
        page_size = kw.get('pageSize') or 100
        order_by = 'schedule_date asc' if state =='pending' else 'write_date desc'

        domain = [('assigned','=',user['id'])]
        if state:
            if state  == 'pending':
             domain.append(('state','in',['pending','shipped']))
             if not date:
                domain.append(('schedule_date','<=',datetime.today()))
            else:
                domain.append(('state','=',state))
        
        if date:
            date = datetime.fromisoformat(date)
            if state =='completed':
                domain.append(('completed_at','>',date.combine(date=date.date(),time=time(0,0,0))))
                domain.append(('completed_at','<',date.combine(date=date.date(),time=time(23,59,59))))
            else:
                domain.append(('schedule_date','<=',date))
        
        user = request.env['res.users'].sudo().browse(user['id'])
        pickings = request.env['delivery_boy.picking'].sudo().search(domain=domain,limit=page_size,offset=(page-1)*page_size,order=order_by)

        
        data = pickings.read(['name','priority','state','schedule_date','delivery_address','sale_id','payment_method','amount_to_collect','total_amount','delivered_amount','sale_id'])
        
        for index,item in enumerate(data):       
            if data[index]['state'] == 'shipped':
                data[index]['state'] = 'pending'     
            data[index]['delivery_address'] =request.env['res.partner'].sudo().search_read([('id','=',item['delivery_address'][0])],['display_name','phone','mobile','city','street','partner_latitude','partner_longitude'],limit=1)[0]   
            data[index]['delivery_address']['phone']= f"{data[index]['delivery_address']['mobile'] or ''} {data[index]['delivery_address']['phone'] or ''}"
        
        return {
                'status':201,
                'data':data,
                "message":"Successfully Fetched Picking !!"
            }


    @http.route('/delivery/api/confirmpicking/<int:id>',type='json',csrf=False, auth='public')
    def confirmPicking(self,id,**kw):
        token = request.httprequest.headers.get('Authorization')

    
        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }
        
        # key value pair of id and value
        items = kw.get('items') 
        user = request.env['res.users'].sudo().browse(user['id'])

        try:
            pickings = request.env['delivery_boy.picking'].sudo().browse(id)            
           
            for line in pickings.sudo().picking_lines:
                line.write({
                    'quantity':items.get(str(line.id))
                })
        
            pickings.with_user(user.id).sudo()._action_completed()

            if kw.get('collectedAmount'):
                pickings.with_user(user.id).sudo()._create_direct_payment(kw['collectedAmount'])
            
            sign_image = kw.get('signature')
            if sign_image:
                pickings.sudo().write({
                    'customer_sign':sign_image.replace("data:image/png;base64,","")
                })

            return {
                    'status':201,
                    'data':None,
                    "message":"Successfully mark as completed !!"
                }
        
        except Exception as e:
            return {
                    'status':500,
                    'data':None,
                    "message":"Something went wrong !!"
                }
            

    @http.route('/delivery/api/pickingdetail',type='json',csrf=False, auth='public')
    def getPickingDetail(self,**kw):
        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }
        
        user = request.env['res.users'].sudo().browse(user['id'])

        id = kw.get('id')

        if not id:
            return {
                'status':400,
                'data':None,
                "message":"Id is compulsory !!"
            }
        try:
            pickings = request.env['delivery_boy.picking'].sudo().browse(id)
            if not pickings:
                return {
                'status':400,
                'data':None,
                "message":"Picking not found !!"
            }

            data = pickings.read(['name','state','schedule_date','delivery_address','sale_id','payment_method','delivered_amount','amount_to_collect','collected_amount','total_amount','sale_id','picking_lines','priority'])

            item = data[0]
            item['delivery_address'] =request.env['res.partner'].sudo().search_read([('id','=',item['delivery_address'][0])],['display_name','phone','city','street'],limit=1)[0]
            

            item['items'] = []

            for line in item['picking_lines']:
                item['items'].append(request.env['stock.move'].sudo().browse(line).read(['product_id','quantity','product_uom_qty','price'])[0])
            
            return {
                    'status':200,
                    'data':data[0],
                    "message":"Successfully fetched data !!"
                }
        
        except Exception as e:
            print(e)
            return {
                    'status':500,
                    'data':None,
                    "message":"Something went wrong !!"
                }
    


    @http.route('/delivery/api/dailysummary',type='json',csrf=False, auth='public')
    def getDailySummary(self,**kw):

        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }

        user = request.env['res.users'].sudo().browse(user['id'])
        
        date = datetime.today()

        domain = [('assigned','=',user['id']),('state','=','completed')]
        domain.append(('completed_at','>',date.combine(date=date.date(),time=time(0,0,0))))
        domain.append(('completed_at','<',date.combine(date=date.date(),time=time(23,59,59))))    

        pickings = request.env['delivery_boy.picking'].sudo().search(domain)

        total_amount = 0 
        for picking in pickings:
            total_amount += picking.delivered_amount
        
        domain = [('assigned','=',user['id']),('state','=','pending'),('schedule_date','<=',date)]

        todaysPending = request.env['delivery_boy.picking'].sudo().search(domain)
        
        todays_product = {}
        
        for pending in todaysPending:
            for line in pending.picking_lines:
                 product_name = line.product_id.name
                 if todays_product.get(product_name):
                     todays_product[product_name] = todays_product[product_name] + line.product_uom_qty
                 else:
                     todays_product[product_name] = line.product_uom_qty
        return {
                    'status':200,
                    'data':{
                        'total_amount':total_amount,
                        'completed':len(pickings),
                        'today':{
                            'remaining':len(todaysPending),
                            'products':todays_product
                        }
                    },
                    "message":"Successfully fetched data !!"
                }



    @http.route('/delivery/api/mypayments',type='json',csrf=False, auth='public')
    def getMyPayments(self,**kw):

        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }

        user = request.env['res.users'].sudo().browse(user['id'])

        date = kw.get('date')
        domain = [('collected_by','=',user['id']),('payment_date','=',date)]

        fields = ['name','partner_id','amount','state','sale_id','picking_id']
       
        payments = request.env['delivery_boy.payment'].sudo().search_read(domain,fields)
        
        total_amount = 0
        for payment in payments:
            total_amount+= payment['amount'] 

        return {
                    'status':200,
                    'data':{
                        'total_amount':total_amount,
                        'payments':payments
                   },
                    "message":"Successfully fetched data !!"
                }


    @http.route('/delivery/api/register/token',type='json',csrf=False, auth='public')
    def registerToken(self,**kw):
        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }

        user = request.env['res.users'].sudo().browse(user['id'])
        
        token = kw.get("deviceToken")

        if not token:
            return {
                'status':400,
                'data':None,
                "message":"Device Token Compulsory !!"
            }
        
        expo_device =  request.env['expo.device'].with_user(SUPERUSER_ID).search([('user_id','=',user.id),('origin_app','=','delivery_boy')],limit=1)

        if expo_device:
            expo_device.expo_push_token= token
        else:
            request.env['expo.device'].with_user(SUPERUSER_ID).create({
                'user_id':user.id,
                'expo_push_token':token,
                'origin_app':'delivery_boy'  
            })

        return {
                'status':200,
                'data':None,
                "message":"Device Token Registered!!"
            }

    @http.route('/delivery/api/remove/token',type='json',csrf=False, auth='public')
    def removeToken(self,**kw):
        token = request.httprequest.headers.get('Authorization')

        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }
        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)
        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }

        user = request.env['res.users'].sudo().browse(user['id'])
        
        expo_device =  request.env['expo.device'].with_user(SUPERUSER_ID).search([('user_id','=',user.id),('origin_app','=','delivery_boy')])

        if expo_device:
            expo_device.unlink()
        
        return {
                'status':200,
                'data':None,
                "message":"Device Token Removed!!"
            }

    @http.route('/delivery/api/signature/<int:id>',type='http',csrf=False, auth='public')
    @make_response
    def submitSignature(self,id,**kw):
       
         
        sign_image = kw.get('image')
        token = request.httprequest.headers.get('Authorization')


        if not token:
             return {
                'status':401,
                'data':None,
                "message":"Token Missing"
            }

        secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
        user = endoceJwt(token.split(' ')[1],secret_key)

        if not user:
            return {
                'status':401,
                'data':None,
                "message":"Token Expired !!"
            }

        # print(image_base64)
        try:
            request.env['delivery_boy.picking'].sudo().search([('id','=',id)],limit=1).write({
                'customer_sign':  sign_image.replace("data:image/png;base64,","")
            })
            
            return {
                "status":201,
                "data":None,
                "message":'Signature Uploaded!!'
            }

        except Exception as e:
            print(e)
            return  {
                "status":500,
                "data":None,
                "message":'Something went wrong!!'
            }
            

        