# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SalesOrderInherit(models.Model):
    _inherit = "sale.order"



    delivery_boy_payments= fields.One2many("delivery_boy.payment","sale_id",string="Collected Cash")
    delivery_boy_payments_count = fields.Integer(compute="_delivery_boy_payments_count",default=0)
    delivery_boy_picking_id = fields.One2many(comodel_name="delivery_boy.picking",inverse_name="sale_id",string="Delivery Boy")
    delivery_boy_status = fields.Char(compute="_compute_delivery_boy_status",string="Delivery Boy Status")
    last_delivery_date = fields.Date(compute="_compute_last_delivery_date",string="Last Delivery Date")
    

    @api.depends('delivery_boy_payments')
    def _delivery_boy_payments_count(self):
        for rec in self:
            rec.delivery_boy_payments_count = len(rec.delivery_boy_payments.filtered(lambda p:p.state !='draft'))

    def _compute_last_delivery_date(self):
        for rec in self:
            last_delivery_picking = self.env['delivery_boy.picking'].search([('partner_id','=',rec.partner_id.id),('state','=','completed')],order='completed_at desc',limit=1)
            rec.last_delivery_date = last_delivery_picking.completed_at


    def action_view_collected_cash(self):
        self.ensure_one()
        payments = self.delivery_boy_payments.filtered(lambda p:p.state !='draft')
        if self.delivery_boy_payments ==1:
           return {
            'name':'Delivery Boy',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery_boy.payment',
            'res_id': payments.id,
        }

        return {
            'name':'Assigned Delivery',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'delivery_boy.payment',
            'domain': [('id', 'in', payments.ids)],
        }

    
    @api.depends('delivery_boy_picking_id')
    def _compute_delivery_boy_status(self):

        for rec in self:
            picking_ids =  rec.delivery_boy_picking_id.filtered(lambda r:r.state != "cancel")
            if picking_ids:
                rec.delivery_boy_status= picking_ids[0].state
            else :
                rec.delivery_boy_status= 'Not Assigned'

