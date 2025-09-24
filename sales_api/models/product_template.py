# -*- coding: utf-8 -*-
from odoo import api,fields,models,_

class ProductTemplate(models.Model):
    _inherit="product.template"

    #minimum order quantity for mobile app
    mobile_minimum_order_quantity = fields.Float(string='Mobile Minimum Order Quantity',help="This field display minimum order quantity, when ordering from Android / ios App")  
    
    
