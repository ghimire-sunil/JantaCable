import json
import requests
from odoo import api, fields, models, _
from ..controllers import ird_functions
from odoo.exceptions import UserError, ValidationError
import logging
import re
from datetime import date, datetime, timedelta
import nepali_datetime
from nepali_datetime import date as nepali_date

from odoo.tools.translate import _

log = logging.getLogger(__name__)


class AccountMoveInherited(models.Model):
    _inherit = "account.move"

    def action_invoice_download_pdf(self):
        if self.move_type in ("out_invoice", "out_refund"):
            return self.env.ref(
                "nepali_ird_integration.action_invoice_pos_report"
            ).report_action(self)
        else:
            return super().action_invoice_download_pdf()

    @api.depends("move_type", "origin_payment_id", "statement_line_id")
    def _compute_journal_id(self):
        for move in self.filtered(
            lambda r: r.journal_id.type not in r._get_valid_journal_types()
        ):
            if move.move_type == "out_invoice":
                move.journal_id = move.company_id.default_invoice_journal_id.id
            else:
                move.journal_id = move._search_default_journal()

    @api.model
    def run_sql_my(self, qry):
        self._cr.execute(qry)

    @api.depends("company_id")
    def _perform_compute_action(self):
        for rec in self:
            if rec.company_id:
                if rec.company_id.ird_integ == True:
                    rec.ird_integ = True
                else:
                    rec.ird_integ = False

    printed_count = fields.Integer(
        default=0, string="Print Count", help="used for invoice printcount", store=True
    )
    bill_post = fields.Boolean(
        string="Sync state", copy=False, tracking=True, default=False
    )
    bill_data = fields.Char(string="Bill Data")
    last_printed = fields.Datetime(
        string="Last Printed", default=lambda self: fields.datetime.now(), tracking=True
    )
    ird_integ = fields.Boolean("Connect to IRD", compute="_perform_compute_action")
    is_realtime = fields.Boolean("Is Realtime", default=False, store=True)
    buyer_pan = fields.Char(related="partner_id.vat")
    non_taxable_sales = fields.Float(default=0.0)
    export_sales = fields.Float(default=0.0)

    check_rev = fields.Selection(related="payment_state", store=True, readonly=True)

    fy_prefix = fields.Char(
        string="Fiscal Year Prefix", compute="_compute_fy_prefix", store=True
    )
    payment_method = fields.Char(
        string="Payment Method", related="payment_ids.journal_id.name"
    )
    entered_by = fields.Char(string="Entered By", related="user_id.name")
    printed_by = fields.Char(string="Printed By", compute="compute_printed_by")
    print_state = fields.Selection(
        [("printed", "Printed"), ("not_printed", "Not Printed")],
        string="Print State",
        default="not_printed",
        compute="_compute_print_state",
    )
    active = fields.Selection(
        [("active", "Active"), ("inactive", "Inactive")],
        string="Active",
        default="active",
        compute="_compute_active_state",
    )
    vat_refund_amount = fields.Float(
        string="VAT Refund Amount", default=0.0, help="Amount of VAT refunded if any"
    )
    transaction_amount = fields.Float(
        string="Transaction Amount", default=0.0, help="Amount of transaction if any"
    )
    move_type = fields.Selection(
        selection_add=[("in_refund", "Vendor Debit Note")],
    )

    def _get_move_display_name(self, show_ref=False):
        self.ensure_one()
        resp = super()._get_move_display_name(show_ref=show_ref)
        if resp == "Draft Vendor Credit Note":
            return "Draft Vendor Debit Note"

        return resp

    @api.depends("printed_count")
    def _compute_active_state(self):
        for record in self:
            if record.printed_count > 0:
                record.active = "active"
            else:
                record.active = "inactive"

    @api.depends("printed_count")
    def _compute_print_state(self):
        for record in self:
            if record.printed_count > 0:
                record.print_state = "printed"
            else:
                record.print_state = "not_printed"

    @api.model
    def post_invoices_ird(self):
        inv_objs = self.env["account.move"].search(
            [
                ("state", "=", "posted"),
                ("move_type", "in", ("out_invoice", "out_refund")),
                ("bill_post", "=", False),
                ("invoice_date", ">=", date(2023, 7, 17)),
            ]
        )
        if inv_objs:
            for invoice in inv_objs:
                comp_obj = self.env["res.company"].search(
                    [("id", "=", invoice.company_id.id)], limit=1
                )
                if comp_obj.ird_integ:
                    fy_yr = comp_obj.fy_prefix
                    if invoice.move_type == "out_invoice":
                        data = {
                            "username": str(comp_obj.ird_user),
                            "password": str(comp_obj.ird_password),
                            "seller_pan": str(invoice.company_id.vat),
                            "buyer_pan": str(invoice.partner_id.vat)
                            if invoice.partner_id.vat
                            else "",
                            "buyer_name": str(invoice.partner_id.name),
                            "fiscal_year": fy_yr,
                            "invoice_number": str(invoice.name),
                            "invoice_date": ird_functions.date_dot_format(
                                invoice.invoice_date
                            ),
                            "total_sales": str(invoice.amount_total),
                            "taxable_sales_vat": str(invoice.amount_untaxed),
                            "vat": str(invoice.amount_tax),
                            "excisable_amount": "0",
                            "excise": "0",
                            "taxable_sales_hst": "0",
                            "hst": "0",
                            "amount_for_esf": "0",
                            "esf": "0",
                            "export_sales": "0",
                            "tax_exempted_sales": "0",
                            "isrealtime": True
                            if invoice.invoice_date == date.today()
                            else False,
                            "datetimeclient": str(date.today()),
                        }
                        res = ird_functions.ir_api_post(
                            json=data, bill_type=invoice.move_type
                        )
                        invoice.bill_data = json.dumps(data) + str(res)
                        if res["response_code"] == "200":
                            invoice.bill_post = True
                            if invoice.invoice_date == date.today():
                                invoice.is_realtime = True

                    elif invoice.move_type == "out_refund":
                        ref_invoice_number = ""
                        reason_for_return = ""
                        try:
                            ref = invoice.ref.split(",", 1)
                            ref_invoice_number = ref[0].split()[2]
                            reason_for_return = ref[1].strip()
                        except:
                            pass
                        data = {
                            "username": str(comp_obj.ird_user),
                            "password": str(comp_obj.ird_password),
                            "seller_pan": str(invoice.company_id.vat),
                            "buyer_pan": str(invoice.partner_id.vat)
                            if invoice.partner_id.vat
                            else "0",
                            "buyer_name": str(invoice.partner_id.name),
                            "fiscal_year": fy_yr,
                            "ref_invoice_number": ref_invoice_number,
                            "credit_note_number": str(invoice.name),
                            "credit_note_date": ird_functions.date_dot_format(
                                invoice.invoice_date
                            ),
                            "reason_for_return": reason_for_return,
                            "total_sales": str(invoice.amount_total),
                            "taxable_sales_vat": str(invoice.amount_untaxed),
                            "vat": str(invoice.amount_tax),
                            "excisable_amount": "0",
                            "excise": "0",
                            "taxable_sales_hst": "0",
                            "hst": "0",
                            "amount_for_esf": "0",
                            "esf": "0",
                            "export_sales": "0",
                            "tax_exempted_sales": "0",
                            "isrealtime": True,
                            "datetimeclient": str(date.today()),
                        }
                        res = ird_functions.ir_api_post(
                            json=data, bill_type=invoice.move_type
                        )
                        invoice.bill_data = json.dumps(data) + str(res)
                        if res["response_code"] == "200":
                            invoice.bill_post = True
                            if invoice.invoice_date == date.today():
                                invoice.is_realtime = True
                    else:
                        raise UserError(
                            _("Invalid date i.e out of current Fiscal Year.")
                        )
                else:
                    pass
        else:
            print("All bills posted to IRD")

    @api.depends("amount_total")
    def get_amount_in_words(self):
        amount_in_words = self.currency_id.amount_to_text(self.amount_total)
        return amount_in_words

    invoice_date = fields.Date(
        string="Invoice/Bill Date",
        index=True,
        copy=False,
        # default=date.today()
    )
    nepali_date = fields.Char(string="Nepali Date", compute="_compute_nepali_date")

    def _get_pos_receipt_filename(self):
        type_string = "Invoice"
        invoice_numbers = self.name or ""
        if self.move_type in ("in_refund", "out_refund"):
            type_string = "Credit_Note"
        filename = (
            "-".join(
                (
                    type_string,
                    invoice_numbers,
                    self.company_id.display_name,
                    self.partner_id.display_name or "",
                )
            )
            .replace(" ", "-")
            .replace(",", "")
            .replace("--", "-")
        )
        return filename

    @api.model
    def increase_print(self):
        if self.state == "posted":
            self.printed_count += 1

    @api.model
    def pos_increase_print(self):
        if self.state == "posted":
            self.pos_printed_count += 1

    def get_printedtime(self):
        return (datetime.now() + timedelta(hours=5, minutes=45)).strftime(
            "%m/%d/%Y %H:%M:%S"
        )

    def get_nepali_bill_date(self):
        if self.invoice_date:
            nepali_date = nepali_datetime.date.from_datetime_date(self.invoice_date)
            sp_date = str(nepali_date).split("-")
            return sp_date[1] + "/" + sp_date[2] + "/" + sp_date[0]
        return ""

    @api.depends("invoice_date")
    def _compute_nepali_date(self):
        for record in self:
            if record.invoice_date:
                nep_date = nepali_date.from_datetime_date(record.invoice_date)
                record.nepali_date = nep_date
            else:
                record.nepali_date = False

    def get_nepali_transaction_date(self):
        if self.invoice_date:
            nepali_date = nepali_datetime.date.from_datetime_date(self.date)
            sp_date = str(nepali_date).split("-")
            return sp_date[1] + "/" + sp_date[2] + "/" + sp_date[0]
        return ""

    def compute_printed_by(self):
        for record in self:
            if record.printed_count > 0:
                record.printed_by = self.env.user.name
            else:
                record.printed_by = ""

    def get_printed_by(self):
        return self.env.user.name

    @api.depends("invoice_date")
    def _compute_fy_prefix(self):
        for record in self:
            if record.invoice_date:
                nep_date = nepali_date.from_datetime_date(record.invoice_date)
                year = nep_date.year
                if nep_date.month >= 4:
                    fy_start = year
                    fy_end = year + 1
                else:
                    fy_start = year - 1
                    fy_end = year
                record.fy_prefix = f"{fy_start}/{str(fy_end)[-2:]}"
            else:
                record.fy_prefix = ""

    def action_print_pdf(self):
        self.ensure_one()
        if self.move_type in ("out_invoice", "out_refund"):
            return self.env.ref(
                "nepali_ird_integration.tax_invoice_nepali"
            ).report_action(self.id)
        else:
            return super().action_print_pdf()


class ResCompanyInherited(models.Model):
    _inherit = "res.company"

    ird_integ = fields.Boolean("Connect to IRD", default=False)
    ird_user = fields.Char("IRD Username")
    ird_password = fields.Char("IRD Password")
    fy_start = fields.Date("Fiscal Year Start")
    fy_end = fields.Date("Fiscal Year End")
    fy_prefix = fields.Char("FY prefix")
    user_manuals = fields.Char("User Manual")


class ResPartnerInherited(models.Model):
    _inherit = "res.partner"

    @api.onchange("vat")
    def _valid_pan(self):
        if self.vat:
            if (len(self.vat) == 0 or len(self.vat) == 9) and self.vat[
                0:
            ].isdigit() == True:
                pass
            else:
                raise ValidationError(_("Invalid Pan Number"))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    nepali_date = fields.Date(compute="_compute_nepali_date")
    invoice_number = fields.Char(related="move_id.name")
    customer_name = fields.Char(related="move_id.partner_id.name")
    buyer_pan = fields.Char(related="move_id.partner_id.vat")
    product_name = fields.Char(related="product_id.name")
    amount_tax = fields.Float(default=0.0, compute="_compute_amount_tax")
    pragyapan_patra = fields.Char()
    pragyapan_patra_date = fields.Date()
    country_id = fields.Char()
    untaxed_amount = fields.Float(default=0.0)
    tax = fields.Char(related="tax_ids.name")

    def _compute_amount_tax(self):
        for line in self:
            line.amount_tax = line.price_total - line.price_subtotal

    @api.depends("invoice_date")
    def _compute_nepali_date(self):
        for record in self:
            if record.invoice_date:
                nep_date = nepali_date.from_datetime_date(record.invoice_date)
                record.nepali_date = nep_date.strftime("%Y-%m-%d")  # Convert to string
            else:
                record.nepali_date = False
