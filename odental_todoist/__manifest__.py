{
    "name": "O Dental - disponibilidad Todoist",
    "summary": "Bloquea en la agenda las reuniones privadas del profesional",
    "version": "18.0.1.4.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_core"],
    "data": [
        "security/ir.model.access.csv",
        "security/odental_todoist_security.xml",
        "data/sync_cron.xml",
        "views/todoist_connection_views.xml",
    ],
    "installable": True,
}
