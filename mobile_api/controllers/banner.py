from odoo import http
from odoo.http import request
from pydantic import ValidationError
from .utils import ALLOWED_URL, response, formate_error
from datetime import date

class BannerImageController(http.Controller):

    @http.route('/api/v1/banner-images', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    def banner_images(self, **kwargs):
        try:
            banner_images = request.env['banner.image'].sudo().search([('published','=',True),('start_date','<=', date.today()), ('end_date', '>=', date.today())])
            data = []
            for banner in banner_images:
                banner_details = {
                    'sequence': banner.sequence,
                    'url': banner.url,
                    'start_date': banner.start_date,
                    'end_date': banner.end_date,
                    'image_1920': banner.image_1920

                }
                data.append(banner_details)
            
            return response(
                status=200,
                message="Banner Details Fetched Successfully",
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