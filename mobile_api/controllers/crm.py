from odoo import http
from odoo.http import request, Response
from pydantic import ValidationError
from .utils import response, required_login, formate_error, check_role, UserRole
from datetime import date, datetime
import json
import base64

class CRMController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/customer/create-crm', type='http', methods=['POST'], auth='public', csrf=False)
    @required_login
    @check_role([UserRole.CUSTOMER.value])
    @make_response
    def create_customer_crm(self, **kwargs):
        try:
            user_id = request.env.user.id
            user = request.env['res.users'].sudo().search([('id','=',user_id)])

            if user.partner_id:
                customer = user.partner_id

                date_deadline = datetime.fromisoformat(kwargs['expected_closing'])

                image_ids = []
                images = request.httprequest.files.getlist('images')

                for image in images:
                    print(image)
                    print(image.filename)
                    image_base64 = base64.b64encode(image.read())
                    image_id = request.env['crm.image'].create({
                        'name': image.filename,
                        'image_1920': image_base64
                    })
                    image_ids.append(image_id.id)

                request.env['crm.lead'].sudo().create({
                    "name": "RFQ requested by - " + customer.name,
                    "partner_id": customer.id,
                    "user_id": customer.user_id.id, 
                    "date_deadline": date_deadline,
                    "description": kwargs['remarks'],
                    "crm_image_ids": [id for id in image_ids]
                })

                return  {
                    'data':{ 
                        "status":200,
                        "data":None,
                        "message":'CRM created successfully!!'
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
                data=None
            )

    @http.route('/api/v1/create-crm', type='http', methods=['POST'], auth='public', csrf=False)
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    @make_response
    def customer_crm(self, **kwargs):
        try:
            user = request.env.user
            customer_id = kwargs['customer_id']

            customer = request.env['res.partner'].sudo().search([('id','=',customer_id)])

            if user.partner_id:

                image_ids = []
                images = request.httprequest.files.getlist('images')

                for image in images:
                    image_base64 = base64.b64encode(image.read())
                    image_id = request.env['crm.image'].create({
                        'name': image.filename,
                        'image_1920': image_base64
                    })
                    image_ids.append(image_id.id)

                request.env['crm.lead'].sudo().create({
                    "name": "RFQ requested by - " + user.name,
                    "partner_id": customer.id,
                    "user_id": user.id, 
                    "date_deadline": date.today(),
                    "description": kwargs['remarks'],
                    "crm_image_ids": [id for id in image_ids]
                })

                customer.is_visited_today = True
                customer.visited_by = user.id

                return  {
                    'data':{ 
                        "status":200,
                        "data":None,
                        "message":'CRM created successfully!!'
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
                data=None
            )

    # @http.route('/api/v1/create-crm', type='json', methods=['POST'], auth='public', csrf=False)
    # @required_login
    # @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    # def create_crm(self, **kwargs):
    #     try:
    #         user = request.env.user
    #         customer_id = kwargs['customer_id']

    #         customer = request.env['res.partner'].sudo().search([('id','=',customer_id)])

    #         if user.partner_id:
    #             request.env['crm.lead'].sudo().create({
    #                 "name": "RFQ requested by - " + user.name,
    #                 "partner_id": customer.id,
    #                 "user_id": user.id, 
    #                 "date_deadline": date.today(),
    #                 "description": kwargs['remarks']
    #             })

    #             return response(
    #                 status=200,
    #                 message="CRM created successfully!!"
    #             )

                 
    #     except ValidationError as error:    
    #         return response(
    #             status=400,
    #             message="Data Validation Error",
    #             data=formate_error(error.errors())
    #         )
        
    #     except Exception as e:
    #         return response(
    #             status=400,
    #             message=e.args[0],
    #             data=None
    #         )