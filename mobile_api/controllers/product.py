import math
from pydantic import ValidationError
from odoo.http import request
from odoo import http

from .schema.product import Product
from .utils import ALLOWED_URL, response, required_login, formate_error
from datetime import date


class ProductController(http.Controller):

    @http.route('/api/v1/products', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def products(self, **kwargs):
        try:
            user = request.env.user
            product_schema = Product(**kwargs)
            ProductTemplate = request.env['product.product'].sudo()
            
            # assign_brands = request.env['user.product.brand'].sudo().search([
            #     ('user_id', '=', request.env.user.id)
            # ]).mapped('brand_ids')
                            
            
            if product_schema.category:
                category = request.env['product.category'].sudo().search([('id','=',product_schema.category)])
                if category.mobile_app_ok:
                    if product_schema.query:
                        products = ProductTemplate.search([    
                            ('mobile_app_ok','=',True), 
                            ('categ_id', '=', product_schema.category),
                            ('name', 'ilike', product_schema.query) 
                        ], limit=product_schema.limit)
                    else:
                        products = ProductTemplate.search([
                            ('mobile_app_ok','=',True),
                            ('categ_id', '=', product_schema.category),
                        ], limit=product_schema.limit)
            else:
                products = ProductTemplate.search([('mobile_app_ok','=',True)],limit=product_schema.limit)
                
            data = []
            for product in products:
                if not product.categ_id.mobile_app_ok:
                    pass
                
                price = product.list_price

                if product_schema.customer_id:
                    customer = request.env['res.partner'].sudo().search([('id','=',product_schema.customer_id)])
                    if customer.property_product_pricelist:
                        pricelist = customer.property_product_pricelist
                        price = pricelist._get_product_price(product, 1) if pricelist else product.list_price
                    else: 
                        pricelist = request.env['product.pricelist'].sudo().search([('default','=',True)], limit=1)
                        if pricelist:
                            price = pricelist._get_product_price(product, 1) if pricelist else product.list_price
                else:
                    if not user.partner_id.property_product_pricelist.default:
                        pricelist = user.partner_id.property_product_pricelist
                        price = pricelist._get_product_price(product, 1) if pricelist else product.list_price

                template = product.product_tmpl_id

                offers = []
                loyalty_programs = request.env['loyalty.program'].sudo().search([('sale_ok', '=', True), ("trigger_product_ids", "in", product.id)])
                for program in loyalty_programs:
                    offers.append({
                        'name': program.name,
                        'program_type': program.program_type,
                        'start_date': program.date_from,
                        'end_date': program.date_to
                    })

                # pricelist = request.env.user.partner_id.property_product_pricelist
                # product_pricelist = request.env['product.pricelist.item'].sudo().search([('product_tmpl_id','=', product.product_tmpl_id.id), ('id', 'in', pricelist.item_ids.ids)])
                # price = product_pricelist._compute_price(
                #     product=product,
                #     quantity=1.0,
                #     uom=product.uom_id,
                #     date=date.today(),
                #     currency=request.env.user.currency_id,
                # )

                data.append({
                    "id": product.id,
                    "product_variant_id": product.id,
                    "name": product.name,
                    "price": product.list_price,
                    "sales_price": price,
                    "category": product.categ_id.name if product.categ_id else None,
                    "internal_reference": product.default_code or "",
                    "barcode": product.barcode or "",
                    "unit": product.uom_name,
                    "on_hand_qty": product.qty_available,
                    "image": f"/web/image/{product._name}/{product.id}/image_1024" if product.image_1024 else None,
                    "currency": product.currency_id.symbol,
                    # "discount": product_pricelist.price,
                    # "price_after_discount": price,
                    "offers": offers    
                })

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

    @http.route('/api/v1/product-category', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def category(self, **kwargs):
        try:
            categories = request.env['product.category'].sudo().search([('mobile_app_ok','=',True)])

            data = []
            # assign_brands = request.env['user.product.brand'].sudo().search([
            #     ('user_id', '=', request.env.user.id)
            # ])
            for category in categories:
                products = request.env['product.template'].sudo().search_count([
                    ('categ_id', '=', category.id),
                    ('mobile_app_ok','=',True)
                ])
                data.append({
                    "id": category.id,
                    "name": category.name,
                    "products_count": products,
                    "image": f"/web/image/product.category/{category.id}/logo"
                })          

            return response(
                status=200,
                message="Product Category Fetch Successfully",
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
        
    @http.route('/api/v1/service-products', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def service_products(self, **kwargs):
        try:
            user = request.env.user
            ProductTemplate = request.env['product.product'].sudo()
            
            products = ProductTemplate.search([('mobile_app_ok','=',True), ('type','=','service')])
                
            data = []
            for product in products:
                if not product.categ_id.mobile_app_ok:
                    pass
                
                price = product.list_price

                if not user.partner_id.property_product_pricelist.default:
                    pricelist = user.partner_id.property_product_pricelist
                    price = pricelist._get_product_price(product, 1) if pricelist else product.list_price

                template = product.product_tmpl_id

                offers = []
                loyalty_programs = request.env['loyalty.program'].sudo().search([('sale_ok', '=', True), ("trigger_product_ids", "in", product.id)])
                for program in loyalty_programs:
                    offers.append({
                        'name': program.name,
                        'program_type': program.program_type,
                        'start_date': program.date_from,
                        'end_date': program.date_to
                    })

                pricelist = request.env.user.partner_id.property_product_pricelist
                product_pricelist = request.env['product.pricelist.item'].sudo().search([('product_tmpl_id','=', product.product_tmpl_id.id), ('id', 'in', pricelist.item_ids.ids)])
                price = product_pricelist._compute_price(
                    product=product,
                    quantity=1.0,
                    uom=product.uom_id,
                    date=date.today(),
                    currency=request.env.user.currency_id,
                )

                data.append({
                    "id": product.id,
                    "product_variant_id": product.id,
                    "name": product.name,
                    "price": product.list_price,
                    "sales_price": price,
                    "category": product.categ_id.name if product.categ_id else None,
                    "internal_reference": product.default_code or "",
                    "barcode": product.barcode or "",
                    "unit": product.uom_name,
                    "on_hand_qty": product.qty_available,
                    "image": f"/web/image/{product._name}/{product.id}/image_1024" if product.image_1024 else None,
                    "currency": product.currency_id.symbol,
                    "discount": product_pricelist.price,
                    "price_after_discount": price,
                    "offers": offers    
                })

            return response(
                status=200,
                message="Service Products Fetched Successfully",
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