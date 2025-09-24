from odoo import api, fields, models

# class DrPaymentWizard(models.TransientModel):
#     _name = 'pdc.payment.wizard'
#     _description = 'pdc Payment Wizard'

#     sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True)
#     name = fields.Char("Name", default='New', readonly=1, tracking=True)
#     # payment_type = fields.Selection(
#     #     [('send_money', 'Send Money')], string="Payment Type", default='send_money', tracking=True)
#     partner_id = fields.Many2one(
#         'res.partner', string="Partner", tracking=True)
#     payment_amount = fields.Monetary("Payment Amount", tracking=True)
#     journal_id = fields.Many2one('account.journal', string="Payment Journal", domain=[
#                                  ('type', '=', 'bank')], required=0, tracking=True)
#     reference = fields.Char("Cheque Reference", tracking=True)

#     # def action_create_dr_payment(self):            
#     #     dr_payment = self.env['dr.payment'].create({
#     #         'sale_order_id': self.sale_order_id.id,
#     #         'total_amount': self.total_amount,
#     #         'dr_amount': self.dr_amount,
#     #         'difference_amount': self.difference_amount,
#     #         'customer_id':self.customer_id.id,
#     #         'reference': self.reference,
#     #     })
#     #     self.sale_order_id.dr_payment_id = dr_payment.id
#     #     return {'type': 'ir.actions.act_window_close'}
    