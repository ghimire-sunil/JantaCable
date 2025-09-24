# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeliveyAssignedWizard(models.TransientModel):
    _name = 'delivery_boy.picking.assigned'
    _description = 'Assigned Picking To Delivery Boy'

    stock_picking_id = fields.Many2one(comodel_name='stock.picking',required=True,string="Delivery")
    assigned = fields.Many2one(comodel_name='res.users',string="Delivery Person",domain="[('is_delivery_person','=',True)]")
    schedule_date = fields.Date(string="Schedule Date",default=lambda self:fields.Date.today())



    def action_create_picking(self):

        picking=self.env['delivery_boy.picking'].create({
            'stock_picking_id':self.stock_picking_id.id,
            'assigned':self.assigned.id,
            'delivery_address':self.stock_picking_id.partner_id.id,
            'sale_id':self.stock_picking_id.sale_id.id,
            'schedule_date':self.schedule_date
        })
        picking._action_confirm()

        return True

  


        

