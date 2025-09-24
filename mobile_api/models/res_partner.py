from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import time

class ResPartnerInherited(models.Model):
    _inherit = "res.partner"

    is_ordered_today = fields.Boolean(default=False)
    is_payment_taken_today = fields.Boolean(default=False)

    is_visited_today = fields.Boolean(default=False)
    visited_by = fields.Many2one("res.users")

    credit_limit_span = fields.Integer('Credit Limit Span')
    credit_limit_span_exceeded = fields.Boolean(compute='_compute_credit_limit_span_exceeded')
    registration_number = fields.Char()
    dealer_reference = fields.Char(string="Dealer Reference")

    role = fields.Selection(
        string="Role",
        selection=[
            ("sale_person", "Sale Person"),
            ("sale_agent", "Sale Agent"),
            ("customer", "Distributor"),
            ("delivery", "Delivery Person"),
        ],
        default="sale_person",
        help="Sale Person :- who take order form customer \n Sale Agent :- who take both payment and order from customer \n Delivery Person : who is responsible for the delivery of products",
    )

    sales_team_ids = fields.One2many("crm.team", "default_distributor_id")

    image_1920 = fields.Image(string="Image")

    # duplicate_bank_partner_ids = fields.Char()

    private_label = fields.Boolean(string="Private Label")
    artwork_reference = fields.Image(string="Artwork Reference")
    lead_time_note = fields.Char(string="Lead Time Note")
    min_order_qty_check = fields.Char(string="Minimum Order Quantity Check")
    packaging_notes = fields.Char(string="Packaging Notes")

    last_ordered_date = fields.Datetime(compute="_compute_last_ordered_date")

    distributor_id = fields.Many2one(
        "res.partner", domain="[('category_id.distributor','=',True)]"
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        if not self.dealer_reference:
            digits = str(int(time.time() * 1000000))[-5:]
            dealer_code = "BHS" + digits

            while self.env['res.partner'].search_count([('dealer_reference', '=', dealer_code)]) > 0:
                digits = str(int(time.time() * 1000000))[-5:]
                dealer_code = "BHS" + digits

            self.dealer_reference = dealer_code

        return res
    
    @api.depends('sale_order_ids')
    def _compute_last_ordered_date(self):
        for partner in self:
            partner.last_ordered_date = False
            last_order = self.env['sale.order'].sudo().search([('id', 'in', partner.sale_order_ids.ids), ('state', '=', 'sale')], order="date_order desc", limit=1)
            if last_order:
                partner.last_ordered_date = last_order.date_order

    @api.model
    def _cron_ordered_today(self):
        customers = self.env["res.partner"].sudo().search([])
        for record in customers:
            record.is_ordered_today = False

    @api.model
    def _cron_visited_today(self):
        customers = self.env["res.partner"].sudo().search([])
        for record in customers:
            record.is_visited_today = False
            record.visited_by = False

    @api.model
    def _cron_payment_taken(self):
        customers = self.env["res.partner"].sudo().search([])
        for record in customers:
            record.is_payment_taken_today = False
    
    def action_view_location(self):
        action = self.env['ir.actions.act_window']._for_xml_id('mobile_api.action_partner_location')
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action

    def _compute_credit_limit_span_exceeded(self):
        for rec in self:
            if rec.credit_limit_span and rec.unpaid_invoice_ids:
                unpaid_invoice = self.env['account.move'].search([('id', 'in', rec.unpaid_invoice_ids.ids), ('move_type', '=', 'out_invoice')], order="invoice_date_due")
                oldest_unpaid_invoice = unpaid_invoice[0]
                current_date = date.today()
                if current_date > oldest_unpaid_invoice.invoice_date_due:
                    oldest_due_span = (current_date - oldest_unpaid_invoice.invoice_date_due).days
                    rec.credit_limit_span_exceeded = True if oldest_due_span > rec.credit_limit_span else False
                else:
                    rec.credit_limit_span_exceeded = False
            else:
                rec.credit_limit_span_exceeded = False

    # %(partner_name)s has reached its credit limit days of: %(credit_limit_span)s days.
    # The oldest invoice for (bill_name) has not been paid for (days) days since the due date."
    def _build_credit_span_warning_message(self, record, current_amount=0.0, exclude_current=False, exclude_amount=0.0):
        partner_id = record.partner_id.commercial_partner_id
        credit_to_invoice = partner_id.credit_to_invoice - exclude_amount
        total_credit = partner_id.credit + credit_to_invoice + current_amount
        if not partner_id.credit_limit_span:
            return ''
        msg = _(
            '%(partner_name)s has reached its credit limit span of %(credit_limit_span)s day(s).',
            partner_name=partner_id.name,
            credit_limit_span=partner_id.credit_limit_span
        )
        unpaid_invoice = self.env['account.move'].search([('id', 'in', partner_id.unpaid_invoice_ids.ids)], order="invoice_date_due")
        oldest_unpaid_invoice = unpaid_invoice[0]
        current_date = date.today()
        oldest_due_span = (current_date - oldest_unpaid_invoice.invoice_date_due).days
        return msg + '\n' + _(
            'The invoice %(name)s has not been paid for %(days)s days since the due date.',
            name=oldest_unpaid_invoice.name,
            days=oldest_due_span
        )

class ResContactCategory(models.Model):
    _inherit = 'res.partner.category'

    mobile_ok = fields.Boolean("Mobile App")
    customer = fields.Boolean("Customer")
    distributor = fields.Boolean("Distributor")

    @api.constrains('customer')
    def _check_customer(self):
        for record in self:
            if record.customer:
                customer_contact = self.env['res.partner.category'].sudo().search([('id','!=',record.id),('customer','=',True)])
                if customer_contact:
                    raise ValidationError("There can only be one customer tag!")
                
    @api.constrains('distributor')
    def _check_distributor(self):
        for record in self:
            if record.customer:
                distributor_contact = self.env['res.partner.category'].sudo().search([('id','!=',record.id),('distributor','=',True)])
                if distributor_contact:
                    raise ValidationError("There can only be one distributor tag!")