from odoo import _, fields, models
import time

class ContainerMovementWizard(models.TransientModel):
    _name = 'container.movement.wizard'

    from_date = fields.Datetime('From', default=time.strftime('%Y-01-01'))
    to_date = fields.Datetime('To', default=time.strftime('%Y-12-31'))
    partner_id = fields.Many2one('res.partner', 'Customer')

    def action_open_window(self):
        self.ensure_one()

        all=self.env['container.movement'].search([])
        for one in all:
            one.unlink()

        container_id = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1).id
        container = self.env['product.product'].sudo().search([('product_tmpl_id', '=', container_id)])

        lines = self.env['stock.move.line'].sudo().search([('picking_partner_id', '=', self.partner_id.id), ('product_id', '=', container.id), '&', ('date','>=',self.from_date), ('date', '<=', self.to_date)])

        context = dict(self.env.context, create=False, edit=False)

        def ref(xml_id):
            proxy = self.env['ir.model.data']
            return proxy._xmlid_lookup(xml_id)[1]

        tree_view_id = ref('container_deposit_records.view_container_movement_tree')

        context.update(partner_id=self.partner_id)
        if self.from_date:
            context.update(date_from=self.from_date)

        if self.to_date:
            context.update(date_to=self.to_date)

        views = [
            (tree_view_id, 'list')
            # (form_view_id, 'form'),
            # (graph_view_id, 'graph')
        ]
        
        for line in lines:
            movement = self.env['container.movement'].sudo().create({
                'balance': 0,
                'line_id': line.id
            })

        return {
            'name': _('Container Movement'),
            'context': context,
            'view_mode': 'list',
            'res_model': 'container.movement',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'target': 'current'
        }