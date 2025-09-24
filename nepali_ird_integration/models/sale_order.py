from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from datetime import date as dt

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.constrains('date_order')
    def _check_order_date(self):
        for record in self:
            if record.date_order:
                # Extract the date part of date_order
                order_date = record.date_order.date() if isinstance(record.date_order, datetime) else record.date_order

                # Get today's date without time part
                today = fields.Date.context_today(self)

                # Compare the order_date with today
                if order_date < today:
                    pass
                    # raise ValidationError("Order date cannot be in the past.")


    def _create_invoices(self, grouped=False, final=False, date=None):
            """ Create invoice(s) for the given Sales Order(s).
            Overridden to add discount_amount_currency and set invoice_date to today.
            """
            # Call the super method to get the existing functionality
            moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)

            for move in moves:
                move.invoice_date = dt.today()  # Set invoice_date to today using the alias

                # Update account.move.line with discount_amount_currency
                for line in move.line_ids:
                    sale_order_line = self.env['sale.order.line'].browse(line.sale_line_ids.ids)
                    if sale_order_line:
                        line.discount_amount_currency = sale_order_line.discount_amount

            return moves


          


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount', precompute=True, store=True)       
    discount = fields.Float(string='Discount (%)', compute='_compute_discount', store=True)

    @api.depends('price_unit', 'discount', 'product_uom_qty')
    def _compute_discount_amount(self):
        for line in self:
            if line.discount:
                # Calculate discount amount from percentage
                line.discount_amount = round((line.price_unit * line.product_uom_qty) * (line.discount / 100),2)
            else:
                # Reset discount_amount if discount is not set
                line.discount_amount = 0.0

    @api.depends('discount_amount', 'price_unit', 'product_uom_qty')
    def _compute_discount(self):
        for line in self:
            if line.price_unit and line.product_uom_qty:
                total_price = line.price_unit * line.product_uom_qty
                if total_price > 0:
                    line.discount = round((line.discount_amount / total_price) * 100,2)
                else:
                    line.discount = 0.0
            else:
                line.discount = 0.0

    @api.onchange('discount')
    def _onchange_discount(self):
        for line in self:
            if line.discount and line.price_unit and line.product_uom_qty:
                # Update discount_amount based on the discount percentage
                line.discount_amount = round((line.price_unit * line.product_uom_qty) * (line.discount / 100),2)

    @api.onchange('discount_amount')
    def _onchange_discount_amount(self):
        for line in self:
            if line.price_unit and line.product_uom_qty:
                # Recalculate the discount field based on the discount_amount
                total_price = line.price_unit * line.product_uom_qty
                if total_price > 0:
                    line.discount = round((line.discount_amount / total_price) * 100,2)
                else:
                    line.discount = 0.0

    @api.onchange('price_unit', 'product_uom_qty','discount_amount')
    def _onchange_price_and_qty(self):
        for line in self:
            # Recalculate discount_amount based on the current discount percentage
            if line.discount:
                line.discount_amount = round((line.price_unit * line.product_uom_qty) * (line.discount / 100),2)
                
                
    @api.onchange('discount', 'product_uom_qty')
    def _onchange_discount_and_qty(self):
        for line in self:
            if line.discount and line.product_uom_qty:
                # Calculate discount amount as (discount % * price) * quantity
                line.discount_amount = round((line.discount / 100) * line.price_unit * line.product_uom_qty, 2)
            else:
                line.discount_amount = 0.0

    # def write(self, vals):
    #     # Call the original write method
    #     result = super(SaleOrderLine, self).write(vals)

    #     # Update discount and discount_amount if necessary
    #     # for line in self:
    #     #     if 'discount_amount' in vals or 'discount' in vals or 'price_unit' in vals or 'product_uom_qty' in vals:
    #     #         line._onchange_discount_amount()
    #     #         line._onchange_discount()

    #     return result




# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
#     @api.constrains('date_order')
    
#     def _check_order_date(self):
#         for record in self:
#             if record.date_order:
#                 # Extract the date part of date_order
#                 order_date = record.date_order.date() if isinstance(record.date_order, datetime) else record.date_order

#                 # Get today's date without time part
#                 today = fields.Date.context_today(self)

#                 # Compare the order_date with today
#                 if order_date < today:
#                     raise ValidationError("Order date cannot be in the past.")
            



class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        today = fields.Date.context_today(self)
        for vals in vals_list:
            # Ensure 'move_type' is 'out_invoice' before checking the invoice date
            if vals.get('move_type') == 'out_invoice':
                # Set the invoice date to today if not provided
                if 'invoice_date' not in vals or not vals.get('invoice_date'):
                    vals['invoice_date'] = today
                
                # Convert invoice_date to date format for comparison
                invoice_date = fields.Date.from_string(vals['invoice_date'])

                # Throw an error if the invoice date is not today
                # if invoice_date != today:
                #     raise ValidationError("The invoice date must be today's date.")

        # Call the super method to create the invoice
        return super(AccountMove, self).create(vals_list)

