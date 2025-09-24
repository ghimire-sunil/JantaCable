# -*- coding: utf-8 -*-
{
    'name': "Employee address Nepal",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Smarten Technologies",
    'website': "https://www.smarten.com.np",


    # for the full list
    'category': 'Employee',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    'post_init_hook': 'post_init_hook',

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/employee_address.xml',
        'views/district.xml',
        'views/municipality.xml',
        'views/province.xml',
        'views/ward.xml'
        
    ],
}

