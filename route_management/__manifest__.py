# -*- coding: utf-8 -*-
{
    'name': "Route Management",

    'summary': "Route Management",

    'author': "Smarten Technologies",
    'website': "https://www.smarten.com.np",

    'category': 'Sale',
    'version': '0.1',

    'depends': [
        'base',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        "views/contact.xml",
        "views/route.xml",  
        "wizard/route_management_schedule.xml",
        "views/user_route_schedule.xml",
        "views/menu.xml",                        
    ],
}

