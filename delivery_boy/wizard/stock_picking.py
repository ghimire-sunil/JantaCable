# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingInherit(models.Model):
    _inherit = "stock.picking"


    delivery_boy_picking_id = fields.One2many(comodel_name="delivery_boy.picking",inverse_name="stock_picking_id",string="Delivery")

    picking_count = fields.Integer(compute="_compute_picking_count")


    def action_open_assigned_wizard(self):
        self.ensure_one()

        rec = self.env['delivery_boy.picking.assigned'].create({
            'stock_picking_id':self.id,
        })

        return {
            'name':'Assigned Delivery',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery_boy.picking.assigned',
            'res_id': rec.id,
            'target': 'new',
        }
  

    @api.depends('delivery_boy_picking_id')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(self.delivery_boy_picking_id.filtered(lambda r:r.state != 'cancel'))



    def action_view_delivery_boy_picking(self):
        self.ensure_one()

        deliveries = self.delivery_boy_picking_id.filtered(lambda r:r.state != "cancel")

        if self.picking_count ==1:
           return {
            'name':'Delivery Boy',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery_boy.picking',
            'res_id': deliveries.id,
        }

        return {
            'name':'Assigned Delivery',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'delivery_boy.picking',
            'domain': [('id', 'in', deliveries.ids)],
        }

        

