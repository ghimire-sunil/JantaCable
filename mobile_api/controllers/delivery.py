from odoo import http
from odoo.http import request

from .utils import ALLOWED_URL, response, required_login, formate_error, check_role, UserRole
from pydantic import ValidationError
from datetime import datetime, time

class DeliveryController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/delivery/picking', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.DELIVERY_PERSON.value])
    def getPicking(self,**kw):
        try:
            state = kw.get('state')
            date = kw.get('date')
            page = kw.get('page') or 1
            page_size = kw.get('pageSize') or 100
            order_by = 'schedule_date asc' if state =='pending' else 'write_date desc'

            domain = [('assigned','=',request.env.user.id)]
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
            
            user = request.env.user
            pickings = request.env['delivery_boy.picking'].sudo().search(domain=domain,limit=page_size,offset=(page-1)*page_size,order=order_by)

            data = pickings.read(['name','priority','state','schedule_date','delivery_address','sale_id','payment_method','amount_to_collect','total_amount','delivered_amount','sale_id'])
            
            for index,item in enumerate(data):       
                if data[index]['state'] == 'shipped':
                    data[index]['state'] = 'pending'     
                data[index]['delivery_address'] =request.env['res.partner'].sudo().search_read([('id','=',item['delivery_address'][0])],['display_name','phone','mobile','city','street','partner_latitude','partner_longitude'],limit=1)[0]   
                data[index]['delivery_address']['phone']= f"{data[index]['delivery_address']['mobile'] or ''} {data[index]['delivery_address']['phone'] or ''}"
            
            return response(
                status=200,
                message="Product Fetched Successfully",
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
            )

    @http.route('/api/v1/delivery/confirm-picking', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.DELIVERY_PERSON.value])
    def confirmPicking(self,**kw):
        try:
            items = kw.get('items') 
            picking_id = kw.get('picking_id')
            user = request.env.user

            pickings = request.env['delivery_boy.picking'].sudo().browse(picking_id)         
           
            for line in pickings.sudo().picking_lines:
                print(line.id)
                line.write({
                    'quantity':items.get(str(line.id))
                })
        
            pickings.with_user(user.id).sudo()._action_completed()

            if pickings.pick_payment:
                if kw.get('collectedAmount'):
                    pickings.with_user(user.id).sudo()._create_direct_payment(kw['collectedAmount'])
                
            sign_image = kw.get('signature')
            if sign_image:
                pickings.sudo().write({
                    'customer_sign':sign_image.replace("data:image/png;base64,","")
                })

            return response(
                status=200,
                message="Successfully marked as completed!!",
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
            )
            

    @http.route('/api/v1/delivery/picking-detail', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.DELIVERY_PERSON.value])
    def getPickingDetail(self,**kw):
        try:
            user = request.env.user
            picking_id = kw.get('picking_id')
            pickings = request.env['delivery_boy.picking'].sudo().browse(picking_id)
            if not pickings:
                raise Exception("Picking not found!!")

            data = pickings.read(['name','state','schedule_date','delivery_address', 'latitude', 'longitude', 'sale_id','payment_method','delivered_amount','amount_to_collect','collected_amount','total_amount','sale_id','picking_lines','priority'])

            item = data[0]
            item['delivery_address'] =request.env['res.partner'].sudo().search_read([('id','=',item['delivery_address'][0])],['display_name','phone','city','street'],limit=1)[0]
            

            item['items'] = []

            for line in item['picking_lines']:
                item['items'].append(request.env['stock.move'].sudo().browse(line).read(['product_id','quantity','product_uom_qty','price'])[0])
            
            return response(
                status=200,
                message="Successfully fetched data !!",
                data=data[0]
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
            )
    


    @http.route('/api/v1/delivery/daily-summary', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.DELIVERY_PERSON.value])
    def getDailySummary(self,**kw):
        try:
            user = request.env.user
            date = datetime.today()

            domain = [('assigned','=',user.id),('state','=','completed')]
            domain.append(('completed_at','>',date.combine(date=date.date(),time=time(0,0,0))))
            domain.append(('completed_at','<',date.combine(date=date.date(),time=time(23,59,59))))    

            pickings = request.env['delivery_boy.picking'].sudo().search(domain)
            remaining_pickings = request.env['delivery_boy.picking'].sudo().search([('assigned','=',user.id), ('state', 'in', ['pending', 'shipped']), ('schedule_date','=',date.today())])

            total_amount = 0 
            for picking in pickings:
                total_amount += picking.delivered_amount

            return response(
                status=200,
                message="Successfully fetched data !!",
                data={
                    'total_amount':total_amount,
                    'completed':len(pickings),
                    'remaining':len(remaining_pickings)
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
            )


    @http.route('/api/v1/delivery/my-payments', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.DELIVERY_PERSON.value])
    def getMyPayments(self,**kw):
        try:
            user = request.env.user

            date = kw.get('date')
            domain = [('collected_by','=',user['id']),('payment_date','=',date)]

            fields = ['name','partner_id','amount','state','sale_id','picking_id']
        
            payments = request.env['delivery_boy.payment'].sudo().search_read(domain,fields)
            
            total_amount = 0
            for payment in payments:
                total_amount+= payment['amount'] 

            return response(
                    status=200,
                    message="Successfully fetched data !!",
                    data={
                        'total_amount':total_amount,
                        'payments':payments
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
            )
            

    # CHECK???
    # @http.route('/delivery/api/register/token',type='json',csrf=False, auth='public')
    # def registerToken(self,**kw):
    #     token = request.httprequest.headers.get('Authorization')

    #     if not token:
    #          return {
    #             'status':401,
    #             'data':None,
    #             "message":"Token Missing"
    #         }
    #     secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
    #     user = endoceJwt(token.split(' ')[1],secret_key)
    #     if not user:
    #         return {
    #             'status':401,
    #             'data':None,
    #             "message":"Token Expired !!"
    #         }

    #     user = request.env['res.users'].sudo().browse(user['id'])
        
    #     token = kw.get("deviceToken")

    #     if not token:
    #         return {
    #             'status':400,
    #             'data':None,
    #             "message":"Device Token Compulsory !!"
    #         }
        
    #     expo_device =  request.env['expo.device'].with_user(SUPERUSER_ID).search([('user_id','=',user.id),('origin_app','=','delivery_boy')],limit=1)

    #     if expo_device:
    #         expo_device.expo_push_token= token
    #     else:
    #         request.env['expo.device'].with_user(SUPERUSER_ID).create({
    #             'user_id':user.id,
    #             'expo_push_token':token,
    #             'origin_app':'delivery_boy'  
    #         })

    #     return {
    #             'status':200,
    #             'data':None,
    #             "message":"Device Token Registered!!"
    #         }

    # @http.route('/delivery/api/remove/token',type='json',csrf=False, auth='public')
    # def removeToken(self,**kw):
    #     token = request.httprequest.headers.get('Authorization')

    #     if not token:
    #          return {
    #             'status':401,
    #             'data':None,
    #             "message":"Token Missing"
    #         }
    #     secret_key =request.env['ir.config_parameter'].sudo().get_param('delivery_boy.secret_key',constant.secret_key) 
    #     user = endoceJwt(token.split(' ')[1],secret_key)
    #     if not user:
    #         return {
    #             'status':401,
    #             'data':None,
    #             "message":"Token Expired !!"
    #         }

    #     user = request.env['res.users'].sudo().browse(user['id'])
        
    #     expo_device =  request.env['expo.device'].with_user(SUPERUSER_ID).search([('user_id','=',user.id),('origin_app','=','delivery_boy')])

    #     if expo_device:
    #         expo_device.unlink()
        
    #     return {
    #             'status':200,
    #             'data':None,
    #             "message":"Device Token Removed!!"
    #         }

    @http.route('/delivery/api/signature/<int:id>', type='http', auth='public', csrf=False, cors=ALLOWED_URL)
    @make_response
    @required_login
    @check_role([UserRole.DELIVERY_PERSON.value])
    def submitSignature(self,id,**kw):
        try:
            sign_image = kw.get('image')
            request.env['delivery_boy.picking'].sudo().search([('id','=',id)],limit=1).write({
                'customer_sign':  sign_image.replace("data:image/png;base64,","")
            })

            return {
                'data':{ 
                    "status":200,
                    "data":None,
                    "message":'Signature uploaded successfully!!'
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
            )
            

        
