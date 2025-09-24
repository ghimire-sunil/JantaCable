{
    "name": "Audit Log",
    "version": "18.0.1.0.0",
    "author": "Smarten Technology",
    "license": "AGPL-3",
    "website": "",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/auditlog_view.xml",
        "views/http_session_view.xml",
        "views/http_request_view.xml",
    ],
    "application": True,
    "installable": True,
}
