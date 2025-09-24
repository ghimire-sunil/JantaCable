# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PaymentRegisterWizard(models.TransientModel):
    _name = 'delivery_boy.payment.register'
    _description = 'Register Payment'

    picking_id = fields.Many2one(comodel_name='delivery_boy.picking',string="Picking")
    collected_by= fields.Many2one(comodel_name='res.users',string="Collected By",domain="[('is_delivery_person','=',True)]")
    payment_date = fields.Date(string="Payment Date",default=lambda self:fields.Date.today())
    amount = fields.Float(string="Amount")


    def action_register_payment(self):
        payment=self.env['delivery_boy.payment'].create({
            'picking_id':self.picking_id.id,
            'collected_by':self.collected_by.id,
            'amount':self.amount,
            'payment_date':self.payment_date
        })
        payment._action_confirm()

        return True

  


        

