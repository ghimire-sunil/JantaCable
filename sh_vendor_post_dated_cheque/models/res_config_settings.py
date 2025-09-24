# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdc_vendor = fields.Many2one('account.account', string="PDC Account for Vendor",
                                 related='company_id.pdc_vendor', readonly=False)
    auto_fill_open_invoice = fields.Boolean(string="Auto Fill open Invoice in PDC on Customer Selection",
                                            related="company_id.auto_fill_open_invoice", readonly=False)
    pdc_operation_type = fields.Selection(
        related="company_id.pdc_operation_type", readonly=False)

    # =============
    # Vendor
    # =============
    is_vendor_due_notify = fields.Boolean('Vendor Due Notification',
                                          related='company_id.is_vendor_due_notify', readonly=False)
    is_notify_to_vendor = fields.Boolean('Notify to Vendor',
                                         related='company_id.is_notify_to_vendor', readonly=False)
    is_notify_to_user_vendor = fields.Boolean('Notify to Internal User',
                                              related='company_id.is_notify_to_user_vendor', readonly=False)
    sh_user_ids_vendor = fields.Many2many('res.users', string='Responsible User ',
                                          related='company_id.sh_user_ids_vendor', readonly=False)
    notify_on_1_vendor = fields.Char('Notify On 1',
                                     related='company_id.notify_on_1_vendor', readonly=False)
    notify_on_2_vendor = fields.Char('Notify On 2',
                                     related='company_id.notify_on_2_vendor', readonly=False)
    notify_on_3_vendor = fields.Char('Notify On 3',
                                     related='company_id.notify_on_3_vendor', readonly=False)
    notify_on_4_vendor = fields.Char('Notify On 4',
                                     related='company_id.notify_on_4_vendor', readonly=False)
    notify_on_5_vendor = fields.Char('Notify On 5',
                                     related='company_id.notify_on_5_vendor', readonly=False)
