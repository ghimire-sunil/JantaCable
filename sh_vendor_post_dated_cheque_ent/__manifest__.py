# Copyright (C) Softhealer Technologies.
{
    "name": "Vendor Post-Dated Cheque(PDC) Management - Enterprise Edition",
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
        "account_accountant", "sh_vendor_post_dated_cheque"
    ],
    "data": [

        'views/pdc_menu.xml',

    ],
    "auto_install": False,
    "application": True,
    "installable": True,
    "images": ['static/description/background.png', ],
    "price": 1,
    "currency": "EUR",

}
