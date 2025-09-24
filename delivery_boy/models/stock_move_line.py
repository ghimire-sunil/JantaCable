# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SalesOrderInherit(models.Model):
    _inherit = "stock.move.line"

    delivery_person_id = fields.Many2one('res.users',related='picking_id.delivery_boy_picking_id.assigned')