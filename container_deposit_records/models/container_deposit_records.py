from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import date, datetime

class ContainerDepositRecords(models.Model):
    _name = 'container.deposit.records'
    _inherit = "mail.thread"

    name = fields.Char(string="Container Deposit Record",default="New", readonly=True)
    sale_id = fields.Many2one(comodel_name="sale.order",string="Sales Order")
    partner_id = fields.Many2one("res.partner",related="sale_id.partner_id",string="Customer", readonly=False, store=True)
    order_date = fields.Datetime(related="sale_id.date_order", string="Order Date", readonly=False, default=datetime.now(), store=True)
    returned_date = fields.Date(string="Returned Date", compute="_compute_returned_price_date")
    container_quantity = fields.Float(string="Container Quantity", compute="_compute_quantity", inverse="_inverse_quantity", store=True, compute_sudo=True)
    unit_price = fields.Float(string="Unit Price", compute="_compute_price", compute_sudo=True)
    total_price = fields.Float(compute="_compute_total_price", string="Total Price")
    delivery_boy = fields.Many2one("res.users", related="sale_id.delivery_boy_picking_id.assigned", readonly=False)
    returned_quantity = fields.Float(string="Returned Quantity", compute="_compute_returned_price_date")
    returned_price = fields.Float(string="Returned Price", compute="_compute_returned_price",default=0)
    delivered_date = fields.Date(string="Delivered Date", compute="_compute_delivered_date")

    status = fields.Selection(
        string = 'Status',
        selection = [
            ('draft', 'Draft'),
            ('delivered', 'Delivered'),
            ('returned', 'Returned')
        ]
    )

    return_status = fields.Selection(
        string = 'Return Status',
        selection = [
            ('partial', 'Partial'),
            ('full', 'Full')
        ],
        compute = '_compute_returned_price_date'
    )

    payment_status = fields.Selection(
        string = 'Payment Status',
        selection = [
            ('not_paid', 'Not Paid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid')
        ],
        compute = '_compute_returned_price'
    )

    return_count = fields.Integer('# Returns', compute='_compute_return_count', default=0)
    payments= fields.One2many("account.payment","container_deposit_id",string="Collected Payments")
    payments_count = fields.Integer(compute="_compute_payments_count",default=0)
    entry_ids = fields.Many2many("account.move", compute="_compute_entry_ids", store=True)
    entry_count = fields.Integer(compute="_compute_entry_count",default=0)
    picking_ids = fields.Many2many("stock.picking", string="Delivery", compute="_compute_deliveries", store=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)

    journal_entry = fields.Boolean()
    # payment_journal_entry = fields.Boolean()

    @api.depends('sale_id.picking_ids')
    def _compute_deliveries(self):
        for record in self:
            record.picking_ids = record.picking_ids
            if record.sale_id and record.sale_id.picking_ids:
                for picking in record.sale_id.picking_ids:
                    record.picking_ids = [(4, picking.id)]


    def _inverse_quantity(self):
        pass


    @api.depends('sale_id')
    def _compute_quantity(self):
        for record in self:
            container = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1)
            record.container_quantity = record.container_quantity

            for sale_order_line in record.sale_id.order_line:
                if sale_order_line.product_template_id.is_container_deposit:
                    record.container_quantity = sale_order_line.product_uom_qty

    @api.depends('sale_id')
    def _compute_price(self):
        for record in self:
            container = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1)
            record.unit_price = container.list_price

            for sale_order_line in record.sale_id.order_line:
                if sale_order_line.product_template_id.is_container_deposit:
                    record.unit_price = sale_order_line.price_unit


    @api.depends('sale_id', 'sale_id.invoice_ids', 'sale_id.invoice_ids.state')
    def _compute_entry_ids(self):
        for record in self:
            record.entry_ids = record.entry_ids
            for invoice in record.sale_id.invoice_ids.filtered(lambda p:p.state !='draft'):
                record.entry_ids = [(4, invoice.id)]


    @api.depends('container_quantity','unit_price')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.container_quantity * record.unit_price


    @api.depends('picking_ids')
    def _compute_returned_price_date(self):

        for record in self:
            quantity = False
            
            date = record.picking_ids[-1].date_done if record.picking_ids else False
            for stock_picking in record.picking_ids.return_ids.move_ids:
                quantity += stock_picking.product_uom_qty

            record.returned_date = date
            record.returned_quantity = quantity

            if record.status != 'returned' or not record.returned_quantity:
                record.return_status = False 
            elif record.returned_quantity != record.container_quantity:
                record.return_status = "partial"
            else:
                record.return_status = "full"


    @api.depends('picking_ids')
    def _compute_delivered_date(self):
        for record in self:
            record.delivered_date = record.picking_ids[0].date_done if record.picking_ids else record.delivered_date


    @api.depends('payments')
    def _compute_returned_price(self):
        for rec in self:
            returned_amount = 0
            for payment in rec.payments.filtered(lambda p:p.state =='paid' or p.state in ['paid','in_process']):
                returned_amount += payment.amount
            rec.returned_price = returned_amount
            if rec.returned_price == 0:
                rec.payment_status = 'not_paid'
            elif rec.returned_price < rec.total_price:
                rec.payment_status = 'partial' 
            else:
                rec.payment_status = 'paid'


    @api.depends('payments')
    def _compute_payments_count(self):
        for rec in self:
            rec.payments_count = len(rec.payments)


    @api.depends('picking_ids.return_ids')
    def _compute_return_count(self):
        for rec in self:
            rec.return_count = len(rec.picking_ids.return_ids)


    @api.depends('entry_ids')
    def _compute_entry_count(self):
        for rec in self:
            rec.entry_count = len(rec.entry_ids)


    def action_open_payment_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Payment',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_account_payment_form').id,
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_payment_type': 'outbound',
                'default_amount': self.total_price - self.returned_price,
                'default_memo': 'Sale Order: ' + str(self.sale_id.name),
                'default_partner_type': 'customer'
            }
        }


    def action_open_return_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Container',
            'res_model': 'container.deposit.records',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


    def action_see_returns(self):
        self.ensure_one()
        if len(self.picking_ids.return_ids) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "views": [[False, "form"]],
                "res_id": self.picking_ids.return_ids.id
            }
        return {
            'name': _('Returns'),
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "views": [[False, "list"], [False, "form"]],
            "domain": [('id', 'in', self.picking_ids.return_ids.ids)],
        }


    def action_view_payments(self):
        self.ensure_one()
        if self.payments_count ==1:
           return {
            'name':'Returned Payment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'res_id': self.payments.id,
        }

        return {
            'name':'Returned Payments',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'domain': [('id', 'in', self.payments.ids)],
        }

    def action_create_journal_entry(self):
        container_id = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1).id
        container = self.env['product.product'].sudo().search([('product_tmpl_id', '=', container_id)])
        property_account_income_id = container.property_account_income_id.id
        journal = self.env['account.journal'].sudo().search([('container_deposit_journal', '=', True)], limit=1)
        account = self.env['account.account'].sudo().search([('container_deposit_account', '=', True)], limit=1)

        if not account:
            raise UserError("Please choose an appropriate account for container deposit transaction!!")
        if not journal:
            raise UserError("Please choose an appropriate journal for container deposit transaction!!")
        
        lines = []
        lines.append((0, 0, {
            'account_id': property_account_income_id,
            'display_type':'product',
            'name': 'Container Deposit',
            'credit': self.total_price,
        }))
        lines.append((0, 0, {
            'account_id': account.id,
            'display_type': 'payment_term',
            'name': 'Container Deposit',
            'debit': self.total_price,
        }))

        entry = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'partner_id': self.partner_id.id,
            'invoice_date': date.today(),
            'date': date.today(),
            'line_ids' : lines
        })

        entry.action_post()
        self.entry_ids = [(4, entry.id)]
        self.journal_entry = True


    # def action_create_payment_journal_entry(self):
    #     container_id = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1).id
    #     container = self.env['product.product'].sudo().search([('product_tmpl_id', '=', container_id)])
    #     property_account_income_id = container.property_account_income_id.id
    #     journal = self.env['account.journal'].sudo().search([('container_deposit_journal', '=', True)])
    #     account = self.env['account.account'].sudo().search([('container_deposit_payment_account', '=', True)])

    #     if not account:
    #         raise UserError("Please choose an appropriate account for container deposit transaction!!")
    #     if not journal:
    #         raise UserError("Please choose an appropriate journal for container deposit transaction!!")
        
    #     lines = []
    #     lines.append((0, 0, {
    #         'account_id': property_account_income_id,
    #         'display_type':'product',
    #         'name': 'Container Deposit',
    #         'debit': self.returned_price,
    #     }))
    #     lines.append((0, 0, {
    #         'account_id': account.id,
    #         'display_type': 'payment_term',
    #         'name': 'Container Deposit',
    #         'credit': self.returned_price,
    #     }))

    #     entry = self.env['account.move'].create({
    #         'move_type': 'entry',
    #         # 'invoice_date_due': date.today(),
    #         'journal_id': journal.id,
    #         'partner_id': self.partner_id.id,
    #         'invoice_date': date.today(),
    #         'date': date.today(),
    #         'line_ids' : lines,
    #         'payment_ids': self.payments.ids
    #     })

    #     entry.action_post()
    #     self.entry_ids = [(4, entry.id)]

    #     self.payment_journal_entry = True


    def create(self,vals):
        res = super(ContainerDepositRecords, self).create(vals)
        if not res.sale_id:
            res.name = self.env['ir.sequence'].next_by_code('container.deposit.records') or "New" 
            picking_type = self.env['stock.picking.type'].sudo().search([('code', '=', 'outgoing')], limit=1)
            destination_location = self.env['stock.location'].sudo().search([('usage', '=', 'customer')], limit=1)
            container_id = self.env['product.template'].sudo().search([('is_container_deposit', '=', True)], limit=1).id
            container = self.env['product.product'].sudo().search([('product_tmpl_id', '=', container_id)])
            values = {
                'partner_id': res.partner_id.id,
                'state': 'assigned',
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': destination_location.id,
                'container_deposit_id': res.id,
                'move_ids': [(0, 0, {
                    'name': container.name,
                    'product_id': container.id,
                    'product_uom_qty': res.container_quantity,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': destination_location.id
                })]
            }
            picking = self.env['stock.picking'].create(values)
            
            res.status = 'draft'
            res.delivered_date = picking.date_done

            res.action_create_journal_entry()
            res.picking_ids = [(4, picking.id)]

        return res

    def action_view_entry(self):
        self.ensure_one()
        if self.entry_count ==1:
           return {
            'name':'Journal Entries',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.entry_ids.id,
        }

        return {
            'name':'Journal Entries',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.entry_ids.ids)],
        }

    
    def action_view_container_delivery(self):
        self.ensure_one()
        if self.picking_ids:
           return {
            'name':'Delivery',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.picking_ids[0].id,
        }

    def action_print_payment_receipt(self):
        # pass
        report = self.env.ref('container_deposit_records.container_report_payment_receipt')
        
        return report.report_action(self.payments)