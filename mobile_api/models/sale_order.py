from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    remarks = fields.Html(
        string="Remarks"
    )   
    payment_method = fields.Selection(
        string="Payment Method",
        selection=[
            ('cash', "Cash"),
            ('fonepay', 'Fonepay'),
            ('cheque', "Cheque")
        ],
        tracking=True,
    )

    latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    longitude = fields.Float(string='Geo Longitude', digits=(10, 7))

    order_image_ids = fields.One2many(
        string="Sales Order Media",
        comodel_name='sale.image',
        inverse_name='order_id',
        copy=True,
    )

    # DELIVERY PORTION
    mobile_delivery_status = fields.Char(compute="_mobile_delivery_status",string="Mobile Delivery Status")  
    expected_delivery_time = fields.Datetime(string="Expected Delivery Date")
    is_completed = fields.Boolean(default=False)
    # payment_method = fields.Char(string="Payment Method",compute="_calculate_payment_method")
    # device_type = fields.Selection([('ios','IOS'),('android','Android')],string="App Type",required=False)
    customer_note = fields.Char(string="Customer Note")

    partner_credit_span_warning = fields.Text(
        compute='_compute_partner_credit_span_warning')

    @api.depends('state','delivery_status','is_completed')
    def _mobile_delivery_status(self):
       for record in self:
            record.mobile_delivery_status='pending'
            if record.state =='sale' and record.delivery_status!='full':
                record.mobile_delivery_status ='inprogress'
            if record.state =='sale' and record.delivery_status =='full':
                record.mobile_delivery_status = 'completed'
            if record.state =='sale' and record.delivery_status =='partial':
                record.mobile_delivery_status = 'partially_delivered'
            if record.delivery_boy_status == 'shipped':
                record.mobile_delivery_status = 'shipped'
            if record.delivery_boy_status == 'pending':
                record.mobile_delivery_status = 'ready_to_send'
            if record.state == 'cancel':
                record.mobile_delivery_status ='cancel'

    # @api.depends('transaction_ids')
    # def _calculate_payment_method(self):
    #    for record in self:
    #         last_transaction = record.sudo().transaction_ids._get_last()
    #         # print(last_transaction,record.display_name)
    #         if last_transaction:
    #         # print(last_transaction.payment_method_code)
    #             if last_transaction.payment_method_id.code =="wire_transfer" or last_transaction.state =='done':
    #                 record.payment_method = last_transaction.payment_method_id.name
    #             else :
    #                 record.payment_method = ''
    #         else:
    #             record.payment_method = ''


    def action_confirm(self):
        for rec in self:
            if rec.partner_credit_span_warning != '':
                raise UserError("This order cannot be confirmed since the customer has reached their Credit Limit Span.")
        return super().action_confirm()

    # %(partner_name)s has reached its credit limit days of: %(credit_limit_span)s days.
    # The oldest invoice for (bill_name) has not been paid for (days) days since the due date."
    @api.depends('company_id', 'partner_id', 'amount_total')
    def _compute_partner_credit_span_warning(self):
        for order in self:
            order.with_company(order.company_id)
            order.partner_credit_span_warning = ''
            show_warning = order.state in ('draft', 'sent') and \
                           order.partner_id.credit_limit_span_exceeded
            if show_warning:
                order.partner_credit_span_warning = self.env['res.partner']._build_credit_span_warning_message(
                    order.sudo(),  # ensure access to `credit` & `credit_limit` fields
                    current_amount=(order.amount_total / order.currency_rate),
                )

    def action_order_complete(self):
       self.ensure_one()
       for rec in self:
         rec.is_completed=True
         rec.locked=True

    def action_order_uncomplete(self):
       self.ensure_one()
       for rec in self:
         rec.locked=False
         rec.is_completed=False


    def _send_payment_succeeded_for_order_mail(self):
      # print('not sending email')
      _logger.info('overiding pending mail')
      self.sudo().action_confirm()
      self.sudo()._send_order_confirmation_mail()
      return None

    
    def action_multiple_confirm(self):
        for rec in self:
            rec.write({
                'state':'sale',
            }) 

class SalesImage(models.Model):
    _name = 'sale.image'
    _description = "Sales Image"
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)

    image_1920 = fields.Binary()

    order_id = fields.Many2one(
        string="Sales Order", comodel_name='sale.order', ondelete='cascade', index=True,
    )

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    discount_in_amount = fields.Float(string='Disc(AMT)', compute="_compute_discount_amount", inverse="_set_discount_amount", store=True)
    # prev_price = fields.Float(string="Previous Price", compute="_compute_prev_price")

    # @api.depends('product_id', 'order_id.partner_id')
    # def _compute_prev_price(self):
    #     for record in self:
    #         recent_orders = self.env['sale.order.line'].sudo().search(
    #             [
    #                 ('id', '!=', record.id),
    #                 ('order_id.partner_id', '=', record.order_id.partner_id.id),
    #                 ('product_id', '=', record.product_id.id),
    #                 ('order_id.state', 'in', ['sale'])
    #             ]
    #         )
    #         recent_orders_sorted = sorted(recent_orders, key=lambda l: l.order_id.date_order, reverse=True)
    #         recent_order = recent_orders_sorted[0] if recent_orders_sorted else False
            
    #         record.prev_price = False
    #         if recent_order:
                # record.prev_price = recent_order.price_unit

    @api.depends('discount', 'price_unit', 'product_uom_qty')
    def _compute_discount_amount(self):
        for line in self:
            if line.price_unit and line.product_uom_qty:
                line.discount_in_amount = (line.price_unit * line.product_uom_qty) * (line.discount / 100)
    
    @api.onchange('discount', 'price_unit', 'product_uom_qty')
    def _onchange_discount(self):
        for line in self:
            if line.price_unit and line.product_uom_qty:
                line.discount_in_amount = (line.price_unit * line.product_uom_qty) * (line.discount / 100)

    @api.onchange('discount_in_amount')
    def _onchange_discount_amount(self):
        for line in self:
            if line.price_unit and line.product_uom_qty:
                line.discount = (line.discount_in_amount / (line.price_unit * line.product_uom_qty)) * 100

    @api.onchange('discount_in_amount')
    def _set_discount_amount(self):
        for line in self:
            if line.price_unit and line.product_uom_qty:
                line.discount = (line.discount_in_amount / (line.price_unit * line.product_uom_qty)) * 100