from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError

class ProductTemplateInherited(models.Model):
    _inherit = 'product.template'

    is_container_deposit = fields.Boolean('Is Container Deposit', store=True)



class DepositRecords(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        record = super(DepositRecords, self).action_confirm()

        if self.state == 'sale':
            for product in self.order_line.product_template_id:
                if product.is_container_deposit:
                    updated_vals = {
                        'name': self.env['ir.sequence'].next_by_code('container.deposit.records') or "New", 
                        'sale_id': self.id,
                        'status': 'draft'
                    }
                    self.env['container.deposit.records'].create(updated_vals)
            
        return record



class StockPickingInherited(models.Model):
    _inherit="stock.picking"

    container_deposit_id = fields.Many2one('container.deposit.records', "Container Deposits", compute="_compute_container_deposits", store=True)

    @api.depends('sale_id')
    def _compute_container_deposits(self):
        for record in self:
            record.container_deposit_id = record.container_deposit_id
            if record.sale_id:
                container = self.env['container.deposit.records'].sudo().search([('sale_id','=', record.sale_id.id)])
                record.container_deposit_id = container.id

    def button_validate(self):
        record = super(StockPickingInherited, self).button_validate()

        if self.container_deposit_id and self.container_deposit_id.status=='draft':
            self.container_deposit_id.sudo().write({
                    'status': 'delivered'
                })

        return record

    def action_view_container_deposit(self):
        self.ensure_one()
        if self.container_deposit_id:
            return {
                'name':'Container Deposit',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'container.deposit.records',
                'res_id': self.container_deposit_id.id,
            }



class StockPickingReturnInherited(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_return(self):
        res = super(StockPickingReturnInherited, self)._create_return()
        for record in self:
            if self.env.context.get('active_id') and self.env.context.get('active_model') == 'container.deposit.records':
                container = self.env["container.deposit.records"].sudo().browse(self.env.context.get('active_id'))
                container.sudo().write({
                    'status': 'returned'
                })
        return res


    @api.model
    def default_get(self, fields):
        res = super(StockPickingReturnInherited, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'container.deposit.records':
            if len(self.env.context.get('active_ids', list())) > 1:
                raise UserError(_("You may only return one picking at a time."))

            container_id = self.env['container.deposit.records'].browse(self.env.context.get('active_id'))
            picking = container_id.picking_ids[0] if container_id.picking_ids else False
            
            if picking.exists():
                res.update({'picking_id': picking.id})
        return res

    @api.depends('picking_id')
    def get_container_product(self):
        for wizard in self:
            product_return_moves = [Command.clear()]
            if not wizard.picking_id._can_return():
                raise UserError(_("You may only return Done pickings."))
            # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
            # default values for creation.
            line_fields = list(self.env['stock.return.picking.line']._fields)
            product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
            for move in wizard.picking_id.move_ids:
                if move.state == 'cancel':
                    continue
                if move.scrapped:
                    continue
                product_return_moves_data = dict(product_return_moves_data_tmpl)
                if move.product_id.product_tmpl_id.is_container_deposit:
                    product_return_moves_data.update(wizard._prepare_stock_return_picking_line_vals_from_move(move))
                    product_return_moves.append(Command.create(product_return_moves_data))
            if wizard.picking_id and not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if wizard.picking_id:
                wizard.product_return_moves = product_return_moves

    @api.depends('picking_id')
    def _compute_moves_locations(self):
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'container.deposit.records':
            self.get_container_product()
        else:
            res = super(StockPickingReturnInherited, self)._compute_moves_locations()