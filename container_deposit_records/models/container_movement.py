from odoo import api, fields, models
import time

class ContainerMovement(models.TransientModel):
    _name = 'container.movement'

    balance = fields.Integer(string="Balance",compute="_compute_balance")
    line_id = fields.Many2one('stock.move.line')
    date = fields.Datetime(related='line_id.picking_id.date_done')
    particulars = fields.Selection(related='line_id.picking_type_id.code')
    reference = fields.Char(related='line_id.reference')
    status = fields.Selection(related='line_id.state')
    location_id = fields.Many2one('stock.location', related='line_id.location_id')
    location_dest_id = fields.Many2one('stock.location', related='line_id.location_dest_id')
    unit_of_measure = fields.Many2one('uom.uom', related='line_id.product_uom_id')
    quantity = fields.Float(related='line_id.quantity')

    
    @api.depends('line_id')
    def _compute_balance(self):
        for record in self:
            if record.particulars == 'incoming':
                container_id = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1).id
                container = self.env['product.product'].sudo().search([('product_tmpl_id', '=', container_id)])

                picking = record.line_id.picking_id.return_id
                returns = picking.return_ids

                # if len(returns)==1:
                #     line = picking.move_line_ids.filtered(lambda p:p.product_id == container)
                #     record.balance = record.quantity -line.quantity
                # else:
                line = picking.move_line_ids.filtered(lambda p:p.product_id == container)
                previous_returns = returns.move_line_ids.filtered(lambda p:p.product_id == container and p.picking_id.date_done < record.date)
                returned_quantity = sum(map(lambda x: float(x.quantity), previous_returns))
                record.balance = line.quantity -( returned_quantity+record.quantity)
            else:
                record.balance = record.quantity

               


