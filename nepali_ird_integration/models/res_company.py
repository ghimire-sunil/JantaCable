from odoo import api, fields, models, _
import logging

log = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    default_invoice_journal_id = fields.Many2one(
        "account.journal", "Default Invoice Journal", domain=[("type", "=", "sale")],
    )