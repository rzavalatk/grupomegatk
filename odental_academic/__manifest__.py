{
    "name": "O Dental Académico",
    "summary": "Rotaciones clínicas, casos estudiantiles y aprobación docente",
    "version": "18.0.1.0.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_offline"],
    "data": [
        "security/odental_academic_groups.xml",
        "security/ir.model.access.csv",
        "security/odental_academic_security.xml",
        "data/odental_academic_sequence.xml",
        "data/odental_academic_cron.xml",
        "views/academic_program_views.xml",
        "views/academic_rotation_views.xml",
        "views/academic_case_views.xml",
        "views/academic_submission_views.xml",
        "views/odental_academic_menus.xml",
    ],
    "application": False,
    "installable": True,
}

