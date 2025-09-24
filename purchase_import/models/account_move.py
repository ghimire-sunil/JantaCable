from odoo import models,fields,api


class AccountInvoice(models.Model):
    _inherit = "account.move"

    pp_no = fields.Char(string="PP No", help="Purchase Order Number")
    grn_no = fields.Char(string="GRN No", help="Goods Receipt Note Number")
    purchase_type = fields.Selection(
        [
            ("local", "Local"),
            ("import", "Import"),
        ],
        string="Purchase Type", default="local",)
    
    doc_mode = fields.Selection(
        [
            ("goods_purchase_capital", "Goods Purchase Capital"),
            ("goods_purchase_others", "Goods Purchase Others"),
        ],
        string="Document Mode",
        help="Select the document mode for the invoice.",
        default="goods_purchase_capital"
    )
    vendor_grn_no = fields.Char(
        string="Vendor GRN No",
        help="Vendor Goods Receipt Note Number"
    )
    vendor_grn_date = fields.Date(
        string="Vendor GRN Date",
        help="Vendor Goods Receipt Note Date")
    storage_location_name = fields.Char(
        string="Storage Location Name",
        help="Name of the storage location for the goods"
    )