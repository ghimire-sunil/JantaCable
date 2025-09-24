# -*- coding: utf-8 -*-
{
    'name': "contact_route",

    'summary': "Delivery Route in Contact",


    'author': "Smarten Technologies",
    'website': "https://www.smarten.com.np",

    'category': 'Uncategorized',
    'version': '17.0',

    'depends': [
        'base',
        'stock',
        'point_of_sale',
    ],

    "data": [
        "security/ir.model.access.csv",
        "views/contact.xml",
        "views/route.xml"
    ],
}
