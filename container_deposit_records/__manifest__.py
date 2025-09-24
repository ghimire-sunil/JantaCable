{
    'name': 'Container Deposit Records',
    'version': '1.0',
    'author': 'Smarten Technologies Pvt. Ltd.',
    'depends': ['base','sale','sale_management','stock','sale_stock','accountant', 'delivery_boy'],
    'data': ['security/ir.model.access.csv',
        'data/sequence.xml',
        'wizard/container_movement_wizard.xml',
        'wizard/container_deposit_refund_wizard.xml',
        'reports/container_deposit_records_template.xml',
        'views/container_movement_view.xml',
        # 'reports/container_deposit_records_template.xml',
        'views/product_template_view.xml',
        'views/menu.xml',
        'views/views.xml',
        'views/stock_picking_view.xml',
        'views/account_view.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}