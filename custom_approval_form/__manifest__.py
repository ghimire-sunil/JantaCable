# -*- coding: utf-8 -*-
{
    'name': "Leave Form",
    'summary': """Custom Leave Approval""",

    'author': "Smarten Technologies Pvt. Ltd.",
    'website': "https://www.smarten.com.np",
    'category': 'Approvals',
    'sequence': '-105',
    'version': '18.1',
    'license': 'LGPL-3',

    'depends': [
        'base','approvals','hr_holidays','hr_attendance','hr',
    ],

    'data': [
        "security/ir.model.access.csv",
        "reports/leave_request_form.xml",
        "views/approval_request_form.xml",
        "wizards/attendance_wizard_views.xml",
        "wizards/attendance_employee_report.xml",
        "reports/salary_advance_request_form.xml",
        "reports/resignation_report_approval.xml",
        "reports/resignation_handover_report.xml",
        "reports/resignation_final_interview_form.xml",
        "data/resignation_approval.xml",
        "reports/resignation_form_activity.xml",
    ],
    'application': True,
    'installable': True,
}