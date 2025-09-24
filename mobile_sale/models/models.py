# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class mobile_sale(models.Model):
    _inherit = "sale.order"
    mobile_delivery_status = fields.Char(
        compute="_mobile_delivery_status", string="Mobile Delivery Status"
    )
    expected_delivery_time = fields.Datetime(string="Expected Delivery Date")
    is_completed = fields.Boolean(default=False)
    payment_method = fields.Selection(
        string="Payment Method",
        selection=[
            ('cash', "Cash"),
            ('fonepay', 'Fonepay'),
            ('cheque', "Cheque")
        ],
        tracking=True,
    )
    device_type = fields.Selection(
        [("ios", "IOS"), ("android", "Android")], string="App Type", required=False
    )
    customer_note = fields.Char(string="Customer Note")

    @api.depends("state", "delivery_status", "is_completed")
    def _mobile_delivery_status(self):
        for record in self:
            record.mobile_delivery_status = "pending"
            if record.state == "sale" and record.delivery_status != "full":
                record.mobile_delivery_status = "inprogress"
            if record.state == "sale" and record.delivery_status == "full":
                record.mobile_delivery_status = "completed"
            if record.state == "sale" and record.delivery_status == "partial":
                record.mobile_delivery_status = "partially_delivered"
            if record.delivery_boy_status == "shipped":
                record.mobile_delivery_status = "shipped"
            if record.delivery_boy_status == "pending":
                record.mobile_delivery_status = "ready_to_send"
            if record.state == "cancel":
                record.mobile_delivery_status = "cancel"

    @api.depends("transaction_ids")
    def _calculate_payment_method(self):
        for record in self:
            last_transaction = record.sudo().transaction_ids._get_last()
            #  print(last_transaction,record.display_name)
            if last_transaction:
                # print(last_transaction.payment_method_code)
                if (
                    last_transaction.payment_method_id.code == "wire_transfer"
                    or last_transaction.state == "done"
                ):
                    record.payment_method = last_transaction.payment_method_id.name
                else:
                    record.payment_method = ""
            else:
                record.payment_method = ""

    def action_order_complete(self):
        self.ensure_one()
        for rec in self:
            rec.is_completed = True
            rec.locked = True

    def action_order_uncomplete(self):
        self.ensure_one()
        for rec in self:
            rec.locked = False
            rec.is_completed = False

    def _send_payment_succeeded_for_order_mail(self):
        # print('not sending email')
        _logger.info("overiding pending mail")
        self.sudo().action_confirm()
        self.sudo()._send_order_confirmation_mail()
        return None

    def action_multiple_confirm(self):
        for rec in self:
            rec.write(
                {
                    "state": "sale",
                }
            )


class Settings(models.TransientModel):
    _inherit = "res.config.settings"

    db_name = fields.Char(
        string="Database Name", config_parameter="mobile_sale.db_name"
    )
    secret_key = fields.Char(
        string="Mobile API Key", config_parameter="mobile_sale.secret_key"
    )


class MobileSaleInvoiceInherit(models.Model):
    _inherit = "account.move"

    def action_show_source_document(self):
        #   print(self.invoice_origin)
        document_refs = self.invoice_origin.split(", ") if self.invoice_origin else []
        #   print(document_refs)
        #   print(self.env['sale.order'].search())
        if self.move_type == "out_invoice":
            return {
                "name": "Sale Orders",
                "view_mode": "list,form",
                "res_model": "sale.order",
                "domain": [
                    ("name", "in", document_refs),
                    ("partner_id", "=", self.partner_id.id),
                ],
                "type": "ir.actions.act_window",
            }
            # print(document_refs,'*************')
        return {
            "name": "Purchase Orders",
            "view_mode": "list,form",
            "res_model": "purchase.order",
            "domain": [
                ("name", "in", document_refs),
                ("partner_id", "=", self.partner_id.id),
            ],
            "type": "ir.actions.act_window",
        }


class ResUserInherit(models.Model):
    _inherit = "res.users"

    last_otp = fields.Integer("Last OTP")

    mobile_public_key = fields.Char("Mobile Public Key")

    def _sent_password_otp(self):
        for rec in self:
            password_reset_template = self.env.ref(
                "mobile_sale.mail_template_user_otp_reset_password",
                raise_if_not_found=False,
            )
            try:
                password_reset_template.send_mail(rec.id, force_send=True)
            except:
                return False

            return True
