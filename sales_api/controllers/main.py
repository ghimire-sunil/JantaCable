from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request, Response
from odoo.addons.website.controllers.main import QueryURL
from ..tools import make_response, eval_request_params
from odoo.osv import expression
from odoo.tools import plaintext2html
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.web.controllers.session import Session
import json
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import AccessError, UserError, AccessDenied
import odoo
import logging
logger = logging.getLogger(__name__)


class CustomSession(Session):
    
    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        return super().authenticate("smarten-technology-aqua-world-main-10794832", login, password, base_location)

class MobileSaleApi(http.Controller):
    """
    API for Odoo mobile Sales App
    For API calls that require session_id cookie,
        - send a JSONRPC request: <baseURI>/web/session/authenticate
            with JSON body:
                {
                "jsonrpc": "2.0",
                    "params": {
                        "db": <db>,
                        "login": <user_email>,
                        "password": <password>
                    }
                }
    """

    @http.route('/api/<string:model>', auth='user', methods=["GET"])
    @make_response()
    def search_read(self, model, latest=False, **kwargs):
        """
        _API [GET]_: /api/<string:model>
        PRE-REQUISITE: session_id cookie (through authentication)
        PURPOSE: Get all the records of a model

        PARAMS:
        :<string:model>: Odoo model, e. g; res.partner, product.product, product.category, res.users, etc.
        :fields [Optional]: list of fields of the model being queried
            - if `fields` parameter is not passed, all the fields (key, value pair) \
                of the model is returned
        :order: sort records by a field name, ascending (asc) order by default, desc for descending order
        :limit: limit the number of records returned
        
        
        EXAMPLES:
        - <baseURI>/api/product.category
        - <baseURI>/api/product.template?fields=['name','standard_price']
        # latest 5 products created on the system
        - <baseURI>/api/product.product?order='id desc'&limit=5
        # Products sorted in ascending order by website price
        - <baseURI>/api/product.category?order='website_price'
        
        RETURNS: JSON response of all the records of the model.
        """

        eval_request_params(kwargs)
        return request.env[model].search_read(**kwargs)
    
    @http.route('/api/<string:model>/<int:id>', auth='user', methods=["GET"])
    @make_response()
    def read(self, model, id, **kwargs):
        """
        API [GET]: /api/<string:model>/<int:id>
        PRE-REQUISITE: session_id cookie (through authentication)
        PURPOSE: Get a record, that matches ID, of the model being queried

        PARAMS:
        :<string:model>: Odoo model, e. g; res.partner, product.template, product.category, res.users, etc.
        :<int:id>: Record ID
        :fields [Optional]: list of fields of the model being queried
            - if `fields` parameter is not passed, all the fields (key, value pair) \
                of the model is returned
        
        EXAMPLES:
        - <baseURI>/api/product.category/1
        - <baseURI>/api/product.template/1?fields=['name','standard_price']
        
        RETURNS: JSON response of the record
        """

        eval_request_params(kwargs)
        result = request.env[model].browse(id).read(**kwargs)
        return result and result[0] or {}
    
    @http.route('/api/product.category/<int:id>/products', auth='user', methods=["GET"])
    @make_response()
    def categ_product_read(self, id, **kwargs):
        """
        :API [GET]: /api/product.category/<int:id>/products
        PRE-REQUISITE: session_id cookie (through authentication)
        PURPOSE: Get all the products that belong to the product category (and its child categories)

        PARAMS:
        <int:id>: Product Category ID
        fields [Optional] = list of fields of the model being queried
            - if `fields` parameter is not passed, all the fields (key, value pair) \
                of the model is returned
        :order: sort records by a field name, ascending (asc) order by default, desc for descending order
        :limit: limit the number of records returned
        
        EXAMPLES:
        - <baseURI>/api/product.category/1/products
        - <baseURI>/api/product.template/1/products?fields=['name','standard_price']
        
        RETURNS: JSON response of all the products that belong to the product category (and its child categories)
        """

        eval_request_params(kwargs)
        result = request.env['product.template'].search(
            [('categ_id', 'child_of', id)]).read(**kwargs)
        return result or {}

    @http.route('/api/create/<string:model>', auth='user', methods=["POST"], csrf=False)
    @make_response()
    def create(self, model, **kwargs):
        """
        :API [POST]: /api/create/<string:model>?vals={}
        PRE-REQUISITE: session_id cookie (through authentication)
        PURPOSE: Create a record for a model, while passing the values

        PARAMS:
        :<string:model>: Odoo model, e. g; res.partner, product.template, product.category, res.users, etc.
        :vals [Required] = list of fields with values to create a record
            - if `vals` parameter is not populated, no new record will be created.
        
        EXAMPLES:
        - <baseURI>/api/create/res.partner?vals={'name':'testuser'}
        - <baseURI>/api/create/sale.order?vals={'partner_id':<value>,'user_id':<value>,'order_line':[(0, 0, {'product_uom_qty':<value>,'name':<value>,'price_unit':<value>,'product_id':<value>})]}
        RETURNS: ID of the record created
        """

        eval_request_params(kwargs)
        return request.env[model].create(**kwargs).id

    @http.route('/api/update/<string:model>/<int:id>', auth='user', methods=["PUT"], csrf=False)
    @make_response()
    def write(self, model, id, **kwargs):
        """
        :API [PUT]: /api/update/<string:model>/<int:id>?vals={}
        PRE-REQUISITE: session_id cookie (through authentication)
        PURPOSE: Update a record, with new values of the fields

        PARAMS:
        :<string:model>: Odoo model, e. g; res.partner, product.template, product.category, res.users, etc.
        :<int:id>: Record ID
        :values [Required] = list of fields with new values
            - if `vals` parameter is not populated, no update will take place.
        
        EXAMPLES:
        - <baseURI>/api/update/sale.order/1?vals={'name':'testuser'}
        RETURNS: True / False
        """

        eval_request_params(kwargs)
        return request.env[model].browse(id).write(kwargs['values'])

    @http.route('/api/delete/<string:model>/<int:id>', auth='user', methods=["DELETE"], csrf=False)
    @make_response()
    def unlink(self, model, id):
        """
        :API [DELETE]: /api/delete/<string:model>/<int:id>
        PRE-REQUISITE: session_id cookie (through authentication)
        PURPOSE: Deletes a record

        PARAMS:
        :<string:model>: Odoo model, e. g; res.partner, product.template, product.category, res.users, etc.
        :<int:id>: Record ID
        
        EXAMPLES:
        - <baseURI>/api/delete/sale.order/1
        RETURNS: True / False
        """

        return request.env[model].browse(id).unlink()
    
    @http.route('/api/signup', auth='public', type='http', methods=["POST"], csrf=False)
    def signup(self, **values):
        """
        :API [POST]: /api/signup
        PARAMS:
        -name=<name>
        -login=<username / email>
        -password=<password>
        :USAGE:
        - <baseURI>/api/signup?name=<name>&login=<username / email>&password=<password>

        PURPOSE: Create a new user through API
        
        RETURNS:
        - 409 if user already exists
        - 400 if input fields(login, name and password) are not supplied properly
        - 200 if user registration is successful
        """

        fields = ['login', 'name', 'password']
        response = {
            'message': 'Supply all the required fields!'
        }
        
        

        logger.info(
            'signup called with values: %s', values
        )

        del values['default_address']
        # Parameters validations
        if not all(field in values for field in fields):
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=400)
        
        for key, value in values.items():
            if not values[key]:
                return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=400)
        
        if request.env['res.users'].sudo().search([('login', '=', values['login'])]):
            response = {
                'message': 'User already exists!'
            }
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=409)
        
        user_obj = request.env['res.users'].sudo()._signup_create_user(values)
        if user_obj:
            response = {
                    'message': 'User created!',
                    'user_id': user_obj.id,
                }
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)
        return response
    
    @http.route('/api/<string:model>/<int:id>/post_comment', auth='user', type='json', methods=["POST"], csrf=False)
    def post_review(self, model, id, **kw):
        """
        :API [POST]: /api/<string:model>/<int:id>/post_comment
        PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                    "message": <message>,
                    "message_type": "comment",
                    "subtype": "mt_comment",
                    "rating_value": <int: normally 1(lowest) to 5(highest)>
                }
            }
        PURPOSE: Post comment on a product
        
        RETURNS:
        - 201 if comment posting is successful
        - 400 if comment is not created due to insufficient parameters
        - error (with response 200) if error occured during comment creation
        """
        nosubscribe = True
        if not all([model, id, request.env.user, kw.get('message', False)]):
            Response.status = '400'
            response = {
                'message': 'Could not create comment!'
            }
            return response
        
        record = request.env[model].browse(id)
        author_id = request.env.user.partner_id.id if request.env.user.partner_id else False
        message = plaintext2html(kw['message'])

        message_obj = record.with_context(mail_create_nosubscribe=nosubscribe).message_post(body=message,
            message_type=kw.pop('message_type', "comment"),
            subtype=kw.pop('subtype', "mt_comment"),
            author_id=author_id,
            **kw)
        
        if message_obj:
            Response.status = '201'
            response = {
                'message': 'Comment created!',
            }
            return response
        
        Response.status = '400'
        response = {
            'message': 'Could not create comment!'
        }
        return response

class MobileSaleApiFetchProduct(http.Controller):
    """ API to fetch publicly available products, without log in. """

    # list of products
    @http.route('/api/fetch/products', auth='public', methods=["GET"])
    @make_response()
    def search_read(self, latest=False, **kwargs):
        """
        :API [GET]: /api/fetch/products
        :PURPOSE: Get all product records, available publicly     
        :USAGE:
        - <baseURI>/api/fetch/products?fields=['name','image_small','uom_id','categ_id','partner_ref']

        :fields [Optional]: list of fields of the model being queried
            - if `fields` parameter is not passed, all the fields (key, value pair) \
                of the product is returned

        RETURNS: JSON response of all the products, fetched from the query.
        
        name%27,*
        %27list_price%27,*
        %27website_price%27,
        %27website_public_price%27,
        %27image_medium%27,*
        %27uom_id%27,*
        %27taxes_id%27,
        %20%27description_sale%27,*
        %27mobile_minimum_order_quantity%27,*
        %27image%27,*
        %20%27website_url%27] *
        """
        eval_request_params(kwargs)
        # Might have to change the model to 'product.product', UPDATE: changed to 'product.product' from 'product.template'
        result = request.env['product.product'].sudo().search_read([('website_published','=',True)],['name','list_price','description_sale','image_1024','website_url','mobile_minimum_order_quantity','uom_id','taxes_id'])
        for res in result:
           res['image']=res['image_1024']
           res['image_medium']=res['image_1024']
           del res['image_1024']
        return result or {}

class MobileSaleWishlist(WebsiteSale):
    """ API to create wishlist on Odoo Ecommerce. """

    @http.route('/api/wishlist/add/<int:product_id>', type='json', auth='public', methods=["POST"], website=True, csrf=False)
    def add_to_mobile_wishlist(self, product_id, price=False, **kw):
        """
        :API [POST]: /api/wishlist/add/<int:product_id>
        :PURPOSE: Creates a wishlist on Odoo eCommerce     
        :USAGE:
        - <baseURI>/api/wishlist/add/60
        :PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                }
            }
        -<int:product_id>: Product of your wish.
        RETURNS: JSON response and ID created.
        """

        if not price:
            compute_currency, pricelist_context, pl = self._get_compute_currency_and_context()
            p = request.env['product.product'].with_context(pricelist_context, display_default_code=False).browse(product_id)
            price = p.website_price

        partner_id = session = False
        if not request.website.is_public_user():
            partner_id = request.env.user.partner_id.id
            search_wishlist = request.env['product.wishlist'].search([('partner_id','=',partner_id),('product_id','=',product_id)])
        else:
            session = request.session.sid
            search_wishlist = request.env['product.wishlist'].search([('session','=',session),('product_id','=',product_id)])
        if not search_wishlist:
            new_wishlist = request.env['product.wishlist'].sudo()._add_to_wishlist(
                pl.id,
                pl.currency_id,
                request.website.id,
                price,
                product_id,
                partner_id,
                session
            )
            args = {'success': True, 'message': 'Wishlist Added!', 'id': new_wishlist.id}
            return args
        else:
            #Response.status = '409 Conflict'
            return {'message': 'Duplicate entry found!'}

    @http.route('/api/wishlist/fetch', auth="public", website=True, methods=["GET"])
    @make_response()
    def get_mobile_wishlist(self, count=False, **kwargs):
        """
        :API [GET]: /api/wishlist/fetch
        :PURPOSE: Reads wishlist from Odoo eCommerce     
        :USAGE:
        - <baseURI>/api/wishlist/fetch
        :fields [Optional]: list of fields of the model being queried
            - if `fields` parameter is not passed, all the fields (key, value pair) \
                of the product is returned
        RETURNS: JSON response of all the wishlist, fetched from the query.
        """

        eval_request_params(kwargs)
        partner_id = session = False
        if not request.website.is_public_user():
            partner_id = request.env.user.partner_id.id
            result = request.env['product.wishlist'].sudo().search_read(domain=[('partner_id','=',partner_id)],**kwargs)
        else:
            session = request.session.sid
            result = request.env['product.wishlist'].sudo().search_read(domain=[('session','=',session)],**kwargs)
        return result or {}

class MobileWebsiteSaleApi(http.Controller):
    """ API to enable features of Odoo Ecommerce. """

    @http.route('/api/cart/add', type="json", auth="public", methods=['POST'], website=True, csrf=False,save_session=False)
    def cart_update(self, set_qty=0, **kw):
        """
        :API [POST]: /api/cart/add
        :PURPOSE: Enables Add to Cart function of Odoo eCommerce     
        :USAGE:
        - <baseURI>/api/cart/add
        :PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                    "product_id": <id of the product>,
                    "add_qty": <quatity of the product>,
                }
            }
        RETURNS: JSON response and ID created.
        """

        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        sale_order._cart_update(
            product_id=kw['product_id'],
            add_qty=kw['add_qty'],
            set_qty=set_qty,
            attributes=self._filter_attributes(**kw),
        )
        result = {'success': True, 'message': 'Cart Updated!', 'id': sale_order.id}
        return result or {}

    def _filter_attributes(self, **kw):
        return {k: v for k, v in kw.items() if "attribute" in k}


    @http.route('/api/confirm_sales_order', type="json", auth="public", methods=['POST'], website=True, sitemap=False)
    def confirm_order(self, **post):
        """
        :API [GET]: /api/confirm_sales_order
        :PURPOSE: For Sales Order Confirmation in Odoo eCommerce     
        :USAGE:
        - <baseURI>/api/confirm_sales_order
        :PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                }
            }
        RETURNS: "All Done!" as a response.
        """

        order = request.website.sale_get_order()

        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)

        return "All Done!"

    @http.route('/api/cart/view', type='http', auth="public", website=True, methods=['GET'])
    def cart(self, **post):
        """
        :API [GET]: /api/cart/view
        :PURPOSE: For viewing shopping cart of Odoo eCommerce     
        :USAGE:
        - <baseURI>/api/cart/view
        RETURNS: JSON data of cart items.
        """

        order = request.website.sale_get_order()
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()
        order_line = []
        for items in order.order_line:
            order_line.append({
                'product_id': items.product_id.id,
                'product_uom_qty': items.product_uom_qty,
                'price_unit': items.price_unit,
                'product_uom': items.product_uom.id,
                'price_subtotal': items.price_subtotal,
                'price_tax': items.price_tax,
                'price_total': items.price_total,
                'mobile_minimum_quantity': items.product_id.mobile_minimum_order_quantity,
            })

        if order and order.state == 'draft':
            values = {
            'id': order.id,
            'partner_id': order.partner_id.id,
            'order_line': order_line,
            'amount_untaxed': order.amount_untaxed,
            'amount_tax': order.amount_tax,
            'amount_total': order.amount_total,
            }
            return Response(json.dumps(values), content_type='application/json;charset=utf-8', status=200)

        else:
            return "No Previous Sales Found, or Sales has been Confirmed."

    @http.route(['/api/cart/shipping'], type='json', auth="public", csrf=False,save_session=False, methods=['POST'], website=True)
    def checkout_shipping(self, **post):
        """
        :API [POST]: /api/cart/shipping
        :PURPOSE: Shipping address provision in shopping cart     
        :USAGE:
        - <baseURI>/api/cart/shipping
        :PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                    "partner_id": <shipping address id>
                }
            }
        RETURNS: JSON data as response.
        """

        values = {'partner_id': post['partner_id']}
        response = WebsiteSale.checkout_values(self, **values)
        if post['partner_id'] in response['shippings'].ids:
            result = {'success': True, 'message': 'Address Updated!', 'response': response}
        else:
            result = False
        return result or {}

    @http.route(['/api/fetch/past_orders'], type='json', auth="public", csrf=False,save_session=False, methods=['POST'])
    def past_orders(self, **post):
        """
        :API [POST]: /api/fetch/past_orders
        :PURPOSE: API to fetch past sales orders for Mobile App.    
        :USAGE:
        - <baseURI>/api/fetch/past_orders
        :PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                    "partner_id": <partner id of the user>
                }
            }
        RETURNS: JSON data as response.
        """

        partner_id = post['partner_id']
        past_sale_orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id),('state', 'not in', ('draft','sent')),('team_id.team_type', '=', 'website'),('product_id', '!=', False)],).read(fields=['date_order','display_name','product_id','cart_quantity','is_abandoned_cart','invoice_status','amount_untaxed','amount_tax','state','amount_total',
        'payment_term_id','picking_policy','delivery_count','partner_shipping_id','payment_acquirer_id','picking_ids'])

        for sale in past_sale_orders:
            delivery_status = []
            picking_ids = sale.get('picking_ids')
            for picking_id in picking_ids:
                delivery_search = request.env['stock.picking'].sudo().search([('id', '=', picking_id)])
                delivery_status.append({'delivery_status': delivery_search.state, 'picking_id': picking_id, 'name': delivery_search.name})
            # set delivery status of an SO based on state of one or more picking_ids
            if delivery_status and all(delivery_state.get('delivery_status') == 'done' for delivery_state in delivery_status):
                order_delivery_status = 'delivered'
            elif delivery_status and any(delivery_state.get('delivery_status') == 'done' for delivery_state in delivery_status):
                order_delivery_status = 'partially_delivered'
            elif delivery_status and any(delivery_state.get('delivery_status') == 'assigned' for delivery_state in delivery_status):
                order_delivery_status = 'ready_to_ship'
            elif delivery_status:
                order_delivery_status = 'draft_delivery'
            else:
                order_delivery_status = 'not_applicable'

            sale.update({'delivery_status': order_delivery_status})

        return past_sale_orders or []

    @http.route('/api/profile_image/update', type="json", auth="public", methods=['POST'], website=True, csrf=False,save_session=False)
    def profile_image_update(self, **kw):
        """
        :API [POST]: /api/profile_image/update
        :PURPOSE: Update Profile Image of a User.    
        :USAGE:
        - <baseURI>/api/profile_image/update
        :PARAMS:
        - JSON BODY
            {
                "jsonrpc": "2.0",
                "params": {
                    "partner_id": <partner id of the user>,
                    "image": <binary image file>
                }
            }
        RETURNS: Partner ID and Name of the profile updated.
        """

        partner_id = kw['partner_id'] 
        image = kw['image']
        contact = request.env['res.partner'].sudo().search([('id','=',partner_id)])
        contact.write({'image': image})
        result = {'success': True, 'message': ('Image Updated for %s'%contact.name), 'id': contact.id}
        return result or {}

class AuthSignupHomeExt(AuthSignupHome):

    @http.route('/api/reset_password', type='http', auth='public', methods=['POST'], csrf=False,save_session=False)
    def mobile_auth_reset_password(self, **kw):
        """
        :API [POST]: /api/reset_password
        :PURPOSE: provision of password reset for portal users.     
        :PARAMS: login=<login / email of the user>
        :USAGE:
        - <baseURI>/api/reset_password?login=<login / email of the user>
        RETURNS: Response result.

        **NOTE: An email will be sent to the provided login, to reset their password. 
        """

        csrf_token = request.csrf_token()
        login = kw['login']

        user = request.env['res.users'].sudo().search([('login','=',login)])
        if user:
            result = self.web_auth_reset_password(self, csrf_token, login)
            response = {'success': True, 'message': 'An email has been sent with credentials to reset your password'}
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)
            #return result
        else:
            response = {'success': False, 'message': 'Reset password: invalid username or email'}
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=409)

class MobileFetchSliderImages(http.Controller):
    """ API to fetch publicly available slider images, without log in. """

    @http.route('/api/fetch/slider_images', auth='public', methods=["GET"])
    @make_response()
    def search_read(self):
        """
        :API [GET]: /api/fetch/slider_images
        :PURPOSE: Gets all slider images for mobile app, available publicly and currently active    
        :USAGE:
        - <baseURI>/api/fetch/slider_images
        RETURNS: JSON response containing id, name, file_type and image.
        """

        result = request.env['mobile.slider'].sudo().search_read(domain=[('active','=',True)], fields=['id','name','file_type','image'])
        return result or {}
