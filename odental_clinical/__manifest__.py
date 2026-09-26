{
    "name": "O Dental Expediente Clínico",
    "summary": "Expediente, antecedentes, evoluciones, diagnósticos y consentimientos",
    "version": "18.0.1.0.1",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_core"],
    "data": [
        "security/odental_clinical_security.xml",
        "security/ir.model.access.csv",
        "data/odental_clinical_sequence.xml",
        "views/clinical_record_views.xml",
        "views/encounter_views.xml",
        "views/consent_views.xml",
        "views/audit_views.xml",
        "views/odental_clinical_menus.xml",
    ],
    "application": False,
    "installable": True,
}

