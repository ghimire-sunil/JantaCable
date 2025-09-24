from odoo import fields, models, _, api

class PaymentLedger(models.Model):
    _inherit="account.payment"

    def payment_ledger(self):
        total_amount = 0
        paid = 0

        invoices = self.env['account.move'].search([('id', 'in', self.invoice_ids.ids)], order='invoice_date asc')
        data = {
            'sales_person': invoices[0].user_id.name,
            'invoices': [],
            'due_amount': sum(invoices.mapped('amount_total'))
        }

        for invoice in invoices:
            invoice_details = {
                'date': invoice.invoice_date,
                'name': invoice.name,
                'reference': "",
                'amount': invoice.amount_total,
                'payments': []
            }

            payments = self.env['account.payment'].sudo().search([('id', 'in', invoice.matched_payment_ids.ids)], order='date, id asc')
            for payment in payments:
                payment_details = {
                    'date': payment.date,
                    'name': payment.name,
                    'reference': payment.memo,
                    'amount': payment.amount
                }
                invoice_details['payments'].append(payment_details)

                paid += payment.amount

            total_amount += invoice.amount_total
            data['invoices'].append(invoice_details)
        
        data['due_amount'] = total_amount - paid

        print(data)

        return data