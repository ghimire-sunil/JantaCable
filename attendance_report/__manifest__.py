# -*- coding: utf-8 -*-
{
    'name': "Attendance Report",
    'summary': """Attendance Report""",

    'author': "Smarten",
    'website': "https://www.smarten.com.np",
    'category': 'Human Resources',
    'sequence': '-105',
    'version': '17.1',
    'license': 'LGPL-3',

    'depends': [
        'resource',
        'hr_attendance',
        'hr'
    ],

    'data': [
        "security/ir.model.access.csv",
        "views/report.xml",
        "report/attendance_filter_pdf.xml",
        "report/report.xml"
    ],
    'application': True,
    'installable': True,
}
