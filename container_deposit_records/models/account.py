from odoo import api, fields, models
from odoo.exceptions import ValidationError
# from .container_deposit_records import action_create_journal_entry

class AccountPaymentInherited(models.Model):
    _inherit = 'account.payment'

    container_deposit_id = fields.Many2one(comodel_name='container.deposit.records', string="Container Deposit")
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            if self.env.context.get('active_id') and self.env.context.get('active_model') == 'container.deposit.records':
                container = self.env["container.deposit.records"].sudo().browse(self.env.context.get('active_id'))
                res.container_deposit_id = container.id
        return res

    @api.constrains('amount')
    def check_amount(self):
        for record in self:
            if self.env.context.get('active_id') and self.env.context.get('active_model') == 'container.deposit.records':
                container = self.env["container.deposit.records"].sudo().browse(self.env.context.get('active_id'))
                remaining_amount = container.total_price - container.returned_price
                if record.amount > remaining_amount:
                    raise ValidationError("Returned amount cannot be greater than the original paid amount.")

    def action_post(self):
        for rec in self:
            super(AccountPaymentInherited, rec).action_post()
            if self.env.context.get('active_id') and self.env.context.get('active_model') == 'container.deposit.records':
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'New Payment',
                    'res_model': 'account.payment',
                    'res_id': rec._origin.id,
                    'view_mode': 'form',
                    'view_id': self.env.ref('account.view_account_payment_form').id,
                    'target': 'current',
                }
            

class AccountInherited(models.Model):
    _inherit = 'account.account'

    container_deposit_account = fields.Boolean('Container Deposit Account')
    # container_deposit_payment_account = fields.Boolean('Container Deposit Payment Account')


class AccountJournalInherited(models.Model):
    _inherit = 'account.journal'

    container_deposit_journal = fields.Boolean('Container Deposit Journal')