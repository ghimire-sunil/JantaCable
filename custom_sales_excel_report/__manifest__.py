# -*- coding: utf-8 -*-
{
    'name': "Custom Sales Excell Report",
    'summary': """Excell Sales Report""",

    'author': "Smarten Technologies Pvt. Ltd.",
    'website': "https://www.smarten.com.np",
    'category': 'Sales',
    'sequence': '-105',
    'version': '18.1',
    'license': 'LGPL-3',

    'depends': [
        'base','sale_management','stock','sale','accountant','account',
    ],

    'data': [
        "security/ir.model.access.csv",
        "wizards/sales_report_wizard.xml",
        "views/sales_report_menu.xml",
    ],
    'application': True,
    'installable': True,
}