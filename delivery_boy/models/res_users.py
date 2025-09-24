# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUserInherit(models.Model):
    _inherit = "res.users"


    is_delivery_person = fields.Boolean("Is a Delivery Person")
