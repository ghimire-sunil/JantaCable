{
    "name": "Salesperson Filter in Accounting Report",
    "version": "1.1",
    "website": "https://www.smarten.com.np",
    "category": "Accounting/Accounting",
    "description": """
        SalesPerson Filter in Accounting Reports
        ==================
    """,
    "author": "Smarten Technologies",
    "depends": ["base", "account_reports"],
    "assets": {
        "web.assets_backend": [
            "account_report_filter_sales_person/static/src/xml/*",
            "account_report_filter_sales_person/static/src/js/filter.js",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
