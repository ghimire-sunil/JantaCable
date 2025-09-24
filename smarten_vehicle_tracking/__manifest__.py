{
    'name': "Smarten Vehicle Tracking",
    'description': """
        This app is responsible for  Track Vehicle 
    """,
    'sequence': '10',
    'author': "Smarten Technologies",
    'website': "smarten.com.np",
    'category': 'Fleet',
    'version': '17.1',
    'depends': [
        'fleet',
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "views/gps.xml",
        "views/config.xml",
        "views/fleet_detail.xml",
        "views/map.xml"
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
