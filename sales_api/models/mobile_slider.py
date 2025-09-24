# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class mobile_slider(models.Model):

    _name = 'mobile.slider'
    _description = 'Images for Mobile App Slider'

    name = fields.Char(string='Name', required=True)
    image = fields.Binary(string='Image', required=True)
    file_type = fields.Selection([('image', 'Image'),('promotional', 'Promotional'),('others', 'Others')], default='image', string='File Type')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
