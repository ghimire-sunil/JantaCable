# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    pdc_vendor = fields.Many2one(
        'account.account', string="PDC Account for Vendor")
    auto_fill_open_invoice = fields.Boolean(
        string="Auto Fill open Invoice in PDC on Customer Selection ")
    pdc_operation_type = fields.Selection([('cancel', 'Cancel Only'), ('cancel_draft', 'Cancel and Reset to Draft'), ('cancel_delete', 'Cancel and Delete')],
                                          default='cancel', string="Opration Type")
    # =============
    # Vendor
    # =============
    is_vendor_due_notify = fields.Boolean('Vendor Due Notification')
    is_notify_to_vendor = fields.Boolean('Notify to Vendor')
    is_notify_to_user_vendor = fields.Boolean('Notify to Internal User')
    sh_user_ids_vendor = fields.Many2many(
        'res.users', relation='sh_user_ids_vendor_company_rel', string='Responsible User ')
    notify_on_1_vendor = fields.Char(string='Notify On 1')
    notify_on_2_vendor = fields.Char(string='Notify On 2')
    notify_on_3_vendor = fields.Char(string='Notify On 3')
    notify_on_4_vendor = fields.Char(string='Notify On 4')
    notify_on_5_vendor = fields.Char(string='Notify On 5')
