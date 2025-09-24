# -*- coding: utf-8 -*-
{
    'name': "delivery_boy",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','delivery','sale_management','sale_stock','mobile_api','expo-notifications'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cron.xml',
        "views/menu.xml",
        'views/views.xml',
        'views/templates.xml',
        'views/sales_search_view.xml',
        'views/sale_order_inherit.xml',
        'wizard/wh_form_inherit.xml',
        'wizard/views.xml',
        'reports/delivery_report.xml',
        'wizard/delivery_report_wizard.xml',
        'reports/payment_report.xml',
        'wizard/payment_report_wizard.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

