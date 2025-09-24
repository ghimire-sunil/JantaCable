# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Vendor Post-Dated Cheque(PDC) Management - Community Edition",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": """Vendor Post Dated Cheque Management, Manage Post Dated Cheque, View Vendor Bill PDC App, List Of PDC Payment, Track PDC Process, Register Vendor Post Dated Cheque Module, Print PDC Report Odoo""",
    "description": """In Vendor bill a post-dated cheque is a cheque written by the supplier(payer) for a date in the future. Whether a post-dated cheque may be cashed or deposited before the date written on it depends on the country. Currently, odoo does not provide any kind of feature to manage post-dated cheque. That why we make this module. This module will help to manage a post-dated cheque. This module provides a button 'Register PDC Cheque' in invoice form view, after click button one 'PDC Payment' wizard will popup, you have must select a bank where you deposit a PDC cheque after register a PDC cheque you can see the list of PDC cheque payment list in the 'Vendor PDC Payment' menu. after register PDC Payment you can deposit or return that cheque. after deposit, if cheque bounced so you can set that payment on 'Bounced' state. You can track that process of PDC Payment in Bank 'General Ledger' as well as journal entries/items. also, print a PDF report of PDC Payment.
 Vendor Post Dated Cheque Management Odoo
Manage Vendor Post Dated Cheque Module, View Vendor PDC In Bill, See List Of PDC Payment Of Vendor, Track PDC Process, Register Post Dated Cheque, Print Vendor PDC Report Odoo.
 Manage Post Dated Cheque, View Vendor Bill PDC App, List Of PDC Payment, Track PDC Process, Register Vendor Post Dated Cheque Module, Print PDC Report Odoo.

""",
    "version": "0.0.1",
    "depends": [
        "account"
    ],
    "data": [
        "data/ir_sequence.xml",
        "data/account_data.xml",
        "data/ir_cron_data.xml",
        "data/mail_templates.xml",
        "security/ir.model.access.csv",
        "security/pdc_security.xml",
        "views/res_config_settings_views.xml",
        "wizard/pdc_payment_wizard_views.xml",
        "wizard/pdc_multi_action.xml",
        "views/account_move_views.xml",
        "report/pdc_wizard_report.xml",
    ],

    "images": ['static/description/background.png', ],
    "live_test_url": "https://youtu.be/j8oBFutV7DY",
    "auto_install": False,
    "application": True,
    "installable": True,
    "price": 30,
    "currency": "EUR",
    "post_init_hook": "post_init_hook"
}
