{
    "name": "O Dental Contingencia Offline",
    "summary": "Agenda cifrada y captura clínica segura durante interrupciones de internet",
    "version": "18.0.1.0.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_ai", "web"],
    "data": [
        "security/odental_offline_security.xml",
        "security/ir.model.access.csv",
        "data/odental_offline_sequence.xml",
        "views/contingency_views.xml",
        "views/portal_templates.xml",
        "views/odental_offline_menus.xml",
    ],
    "application": False,
    "installable": True,
}

