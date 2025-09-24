{
    "name": "Global Discount",
    "version": "1.0.0",
    "category": "Purchase",
    "summary": "",
    "description": """
    Purchase Order Global Discount (Same as Odoo Sales Discount)
""",
    "license": "OPL-1",
    "author": "Smarten Technology Pvt.Ltd",
    "depends": ["purchase", "sale", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order_view.xml",
        "views/purchase_order_report.xml",
        "views/sale_order_view.xml",
        "views/account_move.xml",
        "wizard/purchase_order_discount_views.xml",
        "wizard/account_move_discount.xml",
    ],
    "installable": True,
    "auto_install": False,
}
