# -*- coding: utf-8 -*-
{
    'name': 'SMS Module',
    'version': '17.1',
    'category': 'SMS',
    'sequence': -200,
    'summary': 'Custom SMS module implemented with custom SMS configuration Server',
    'description': """Custom SMS module implemented with custom SMS configuration Server""",
    'author': 'Smarten Technologies',
    'website': '',
    'depends': [
        'base',
        'contacts',
        'mass_mailing_sms',
        'phone_validation',
    ],
    'data': [

        "security/ir.model.access.csv",
        'views/res_config_settings_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'assets': {
    },
    'license': 'AGPL-3'

}
