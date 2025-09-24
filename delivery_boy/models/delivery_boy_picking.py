# -*- coding: utf-8 -*-

from odoo import models, fields, api,Command
from odoo.exceptions import UserError
from datetime import datetime


class DeliveryPicking(models.Model):
    _name = 'delivery_boy.picking'
    _description = 'Delivery Boy Picking'
    _inherit = "mail.thread"

    name = fields.Char(string="Picking Sequence",default="New")
    stock_picking_id = fields.Many2one(comodel_name='stock.picking',required=True,string="Delivery",domain=[('picking_type_code','=','outgoing')])
    sale_id = fields.Many2one(comodel_name="sale.order",string="Sales Order")
    payment_method = fields.Selection(related="sale_id.payment_method",string="Payment Method")
    total_amount = fields.Monetary(related='sale_id.amount_total',string="Total Amount",store=True,tracking=True)
    amount_to_collect = fields.Monetary(compute="_amount_to_collect",store=False,string="Amount To Collect",help="amount to collect during delivery")
    collected_amount = fields.Monetary(compute="_collected_amount",string="Collected Amount",help="Collected amount during delivery")
    delivery_address= fields.Many2one(comodel_name="res.partner",string="Delivery Address")
    state = fields.Selection([('draft','Draft'),('pending','Pending'),('shipped','Shipped'),('completed','Completed'),('cancel','Cancelled')],string='Status',default="draft",tracking=True)
    assigned = fields.Many2one(comodel_name='res.users',required=True,string="Delivery Person",domain="[('is_delivery_person','=',True)]",tracking=True)
    payments= fields.One2many("delivery_boy.payment","picking_id",string="Collected Payments")
    payments_count = fields.Integer(compute="_payments_count",default=0)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        store=True,
        ondelete='restrict',
        default = lambda self:self.env.company.currency_id.id
    )
    schedule_date = fields.Date(string="Schedule Date",default=lambda self:fields.Date.today())
    partner_id = fields.Many2one("res.partner",related="stock_picking_id.partner_id",string="Customer")
    picking_lines = fields.One2many(comodel_name="stock.move",related='stock_picking_id.move_ids',string="Pickings")
    completed_at = fields.Datetime(string="Completed At",default=None)
    delivered_amount = fields.Monetary(compute="_delivered_amount",string="Delivered Amount",help="Delivered Amount during delivery")
    priority = fields.Selection([('low','Low'),('normal','Normal'),('high','High')],default="normal")
    delivery_street= fields.Char(string="Location",related='delivery_address.street')

    customer_sign = fields.Image(string="Customer Signature")

    
    
    def unlink(self):
        for rec in self:
            if rec.state !="cancel":
                raise UserError("You must first cancel the picking before delete !!")
        
        return super().unlink()


    @api.depends('sale_id')
    def _amount_to_collect(self):
        for rec in self:
            if rec.sale_id:
                rec.amount_to_collect=(rec.sale_id.amount_total-rec.sale_id.amount_paid)
            else:
                rec.amount_to_collect=0

    @api.depends('payments')
    def _collected_amount(self):
        for rec in self:
            sum = 0
            for payment in rec.payments.filtered(lambda p:p.state !='draft'):
                sum += payment.amount
            rec.collected_amount =sum

    @api.depends('picking_lines')
    def _delivered_amount(self):
        for rec in self:
            sum = 0
            for move in rec.picking_lines:
                sum += move.quantity*move.price
            rec.delivered_amount =sum

    @api.depends('payments')
    def _payments_count(self):
        for rec in self:
            rec.payments_count = len(rec.payments.filtered(lambda p:p.state !='draft'))

    # @api.depends('stock_picking_id')
    @api.onchange('stock_picking_id')
    def _on_change_stock_picking(self):
        if self.stock_picking_id:
            self.sale_id = self.stock_picking_id.sale_id
            self.delivery_address =self.stock_picking_id.partner_id

    
    def action_view_payments(self):
        self.ensure_one()
        payments = self.payments.filtered(lambda p:p.state !='draft')
        if self.payments_count ==1:
           return {
            'name':'Delivery Boy',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery_boy.payment',
            'res_id': payments.id,
            # 'target': 'new',
        }

        return {
            'name':'Assigned Delivery',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'delivery_boy.payment',
            'domain': [('id', 'in', payments.ids)],
            # 'target': 'new',
        }


    def action_open_payment_wizard(self):
        self.ensure_one()

        rec = self.env['delivery_boy.payment.register'].create({
            'picking_id':self.id,
            'amount':self.amount_to_collect-self.collected_amount
        })

        return {
            'name':'Register Payment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery_boy.payment.register',
            'res_id': rec.id,
            'target': 'new',
        }
  


    def action_completed(self):
        for rec in self:
            rec._action_completed()

    def action_shipped(self):
        for rec in self:
            if rec.state != 'pending':
                raise UserError("You can only shipped pending orders")
            rec._action_shipped()
            
    def action_confirm(self):
        for rec in self:
            rec._action_confirm()

            if rec.schedule_date == datetime.today():
                rec._send_push_notification(title="New Delivery",body=f"You have been assigned a new delivery:{rec.name}",data={
                    'navigate':"Orders",
                })


    def action_cancelled(self):
        for rec in self:
            rec._action_cancelled()
            rec._send_push_notification(title="Order Cancelled",body=f"{rec.name} has got cancelled")


    def set_to_draft(self):
        for rec in self:
            rec._set_to_draft()


#   business logic

    def _reconcile_after_done(self):
        """
         override this method to do extra things after order completed
         don't forgot to use super to maintain continous chaining
        """

        if self.stock_picking_id.state != 'done':
            self.stock_picking_id\
                .with_context(skip_backorder=True)\
                .button_validate()

    def _quick_match_quantity(self):
        self.ensure_one()
        for line in self.picking_lines:
               line.write({
                'quantity':line.demand
               })
                
    def _action_completed(self):
            self.ensure_one()
            # for line in self.picking_lines:
            #     if line.demand == 0:
            #         raise UserError("Set quantity more than 0 !!")
            self.write({
                'completed_at': datetime.now(),
                'state':'completed'
            })
            
            self._reconcile_after_done()
            # print('calling')

    def _action_cancelled(self):
            self.state = 'cancel'

    def _action_shipped(self):
            self.state = 'shipped'

    def _set_to_draft(self):
            self.state = 'draft'

    def _action_confirm(self):
        if self.name == 'New':
            self.name = self.env['ir.sequence'].next_by_code('delivery_boy.picking') or "New"
        self.state = 'pending'

    
    def _create_direct_payment(self,amount=False):
        self.ensure_one()

        payment=self.env['delivery_boy.payment'].create({
            'picking_id':self.id,
            'collected_by':self.env.user.id,
            'amount':amount or self.amount_to_collect,
        })
        payment._action_confirm()


    def _send_push_notification(self,**kwargs):

        self.ensure_one()
        try:
            expo_device =  self.env['expo.device'].search([('user_id','=',self.assigned.id),('origin_app','=','delivery_boy')])


            if expo_device:
                self.env['expo.message'].create({
                    "device_id":expo_device.id,
                    'title':kwargs['title'],
                    'body':kwargs['body'],
                })._send_notification(**kwargs)
                
        except Exception as e:
            print(e)


    @api.model
    def _cron_daily_remainder(self):

        delivery_boys = self.env['res.users'].sudo().search([('is_delivery_person','=',True)])
        
        for boy in delivery_boys:
            picking_count = self.env['delivery_boy.picking'].sudo().search_count([['assigned','=',boy.id],['state','=','pending'],['schedule_date','=',datetime.today()]])

            expo_device =  self.env['expo.device'].search([('user_id','=',boy.id),('origin_app','=','delivery_boy')])

            if expo_device and picking_count>0:
                try:
                        self.env['expo.message'].create({
                            "device_id":expo_device.id,
                            'title':f"Let's Go!! {boy.name}",
                            'body':f"You have already {picking_count} delivery for Today",
                        })._send_notification()
                except Exception as e:
                    print(e)
