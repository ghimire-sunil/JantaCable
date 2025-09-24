# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Nepal - Accounting',
    'icon': '/account/static/description/l10n.png',
    'countries': ['np'],
    'author': 'Smarten Technologies Pvt. Ltd.',
    'version': '1.0',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """
Nepal accounting chart and localization.
=======================================================
    """,
    'depends': [
        'base',
        'account',
        'accountant',
        'account_reports',
        'stock_account',
    ],
    'data': [
        'data/l10n_np_data.xml',
        'data/res.bank.csv',
        "data/res.country.state.csv",
        'views/report_invoice_templates.xml',
        'views/account_move.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'demo': [
        'demo/demo_company.xml',
    ],
    'license': 'LGPL-3',
}

