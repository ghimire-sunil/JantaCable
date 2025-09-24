# -*- coding: utf-8 -*-
{
    'name': "Custom Ledger",
    'summary': """Custom Ledger Gaur""",

    'author': "Smarten Technologies",
    'website': "https://www.smarten.com.np",
    'category': '',
    'sequence': '-105',
    'version': '18.1',
    'license': 'LGPL-3',

    'depends': [
        'base','account','accountant',
    ],

    'data': [
        # "security/ir.model.access.csv",
        "reports/payment_ledger.xml",
        "reports/thermal_payment_ledgert.xml"
    ],
    'application': True,
    'installable': True,
}