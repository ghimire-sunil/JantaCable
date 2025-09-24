# -*- coding: utf-8 -*-
{
    "name": "vctsdri Automation",
    "summary": "Automation Vctsdri",
    "author": "Smarten Technologies",
    "website": "https://www.smarten.com.np",
    "maintainer": "Gaurav Pandey",
    "category": "Stock",
    "version": "1.0",
    "depends": ["base", "fleet", "stock"],
    "external_dependencies": {"python": ["selenium"]},
    "data": [
        "data/district.xml",
        "data/fleet_data.xml",
        "data/sequence.xml",
        "security/ir.model.access.csv",
        "views/fleet_vehicle_views.xml",
        "views/res_company_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml"
    ],
    "license": "LGPL-3",
    "installable": True,
    "icon": "/vctsdri_automation/static/description/logo.png",
    "countries": ["np"],
}
