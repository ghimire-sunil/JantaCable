# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Purchase Import",
    "version": "18.0",
    "summary": "Purchase Import",
    "category": "Purchase",
    "author": "Smarten Technologies Pvt. Ltd.",
    "website": "https:smarten.com.np",
    "license": "AGPL-3",
    "data": [
        # "security/ir.model.access.csv",
        "views/account_move_views.xml",
    ],
   
    "depends": [
        "base",
        "account",
        "accountant",
        
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    # 'images': ['static/description/banner.png'],
}
