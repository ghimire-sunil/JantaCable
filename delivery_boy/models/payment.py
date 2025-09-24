# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeliveryPayment(models.Model):
    _name = 'delivery_boy.payment'
    _description = 'Delivery Boy Payment'
    _inherit = "mail.thread"


    name = fields.Char(string="Sequence",default="New")
    picking_id = fields.Many2one(comodel_name='delivery_boy.picking',required=True,string="Picking")
    collected_by = fields.Many2one(comodel_name='res.users',required=True,string="Collected By",domain="[('is_delivery_person','=',True)]")
    state = fields.Selection([('draft','Draft'),('pending','Pending'),('posted','Posted')],required=True,default="draft",tracking=True)
    verified_by = fields.Many2one(comodel_name='res.users',string="Verified By")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        store=True,
        ondelete='restrict',
        default = lambda self:self.env.company.currency_id.id
    )
    sale_id = fields.Many2one(comodel_name="sale.order",store=True,compute="_compute_sale_id",string="Sales Order")
    payment_date = fields.Date(string="Payment Date",default=lambda self:fields.Date.today())
    amount = fields.Monetary(string="Amount")
    partner_id = fields.Many2one('res.partner',related='sale_id.partner_id',string="Customer")


    @api.onchange('picking_id')
    def _on_change_picking_id(self):
        if self.picking_id:
            self.collected_by = self.picking_id.assigned.id
            self.amount = self.picking_id.total_amount

    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = self.env.company.currency_id.id
    
    @api.depends('picking_id')
    def _compute_sale_id(self):
        for rec in self:
            rec.sale_id = rec.picking_id.sale_id.id

    def action_confirm(self):
        for rec in self:
            rec._action_confirm()

    

    def action_verified(self):
        for rec in self:
            rec._action_verified()

    def reset_to_draft(self):
        for rec in self:
            rec._reset_to_draft()

    def _action_verified(self):
        self.verified_by = self.env.user.id
        self.state = 'posted'

    def _reset_to_draft(self):
        self.state = 'draft'


    def _action_confirm(self):
        if self.name == 'New':
            self.name = self.env['ir.sequence'].next_by_code('delivery_boy.payment') or "New"
        self.state = 'pending'
    
    