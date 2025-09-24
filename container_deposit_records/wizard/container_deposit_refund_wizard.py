from odoo import _, fields, models
import time

class ContainerDepositRefundWizard(models.TransientModel):
    _name = 'container.deposit.refund.wizard'

    from_date = fields.Datetime('From', default=time.strftime('%Y-01-01'))
    to_date = fields.Datetime('To', default=time.strftime('%Y-12-31'))
    partner_id = fields.Many2one('res.partner', 'Customer')

    def action_open_window(self):
        self.ensure_one()

        all=self.env['container.deposit.refund.wizard'].search([])
        for one in all:
            one.unlink()

        # container_id = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1).id
        # container = self.env['product.product'].sudo().search([('product_tmpl_id', '=', container_id)])

        # lines = self.env['account.move.line'].sudo().search([('picking_partner_id', '=', self.partner_id.id), ('product_id', '=', container.id), '&', ('date','>=',self.from_date), ('date', '<=', self.to_date)])

        context = dict(self.env.context, create=False, edit=False)

        def ref(xml_id):
            proxy = self.env['ir.model.data']
            return proxy._xmlid_lookup(xml_id)[1]

        # tree_view_id = ref('container_deposit_records.view_container_deposit_refund_tree')

        context.update(partner_id=self.partner_id)
        if self.from_date:
            context.update(date_from=self.from_date)

        if self.to_date:
            context.update(date_to=self.to_date)

        # views = [
        #     (tree_view_id, 'list')
        # ]
        
        # for line in lines:
        #     deposit_refund = self.env['container.deposit.refund.wizard'].sudo().create({
        #         'balance': 0,
        #         'line_id': line.id
        #     })

        # def get_excel_report(self):
        #     # redirect to /sale/excel_report controller to generate the excel file
        #     return {
        #         'type': 'ir.actions.act_url',
        #         'url': '/sale/excel_report/%s' % (self.id),
        #         'target': 'new',
        #     }
    def action_get_excel_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/container_deposit/excel_report/%s' % (self.id),
            'target': 'new',
        }

        # return {
        #     'name': _('Container Deposit Refund'),
        #     'context': context,
        #     'view_mode': 'list',
        #     'res_model': 'container.movement',
        #     'type': 'ir.actions.act_window',
        #     'views': views,
        #     'view_id': False,
        #     'target': 'current'
        # }