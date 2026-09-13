{
    "name": "O Dental Referencias y Acceso Temporal",
    "summary": "Referencias selectivas con consentimiento, doble factor y auditoría",
    "version": "18.0.1.0.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_treatment", "portal"],
    "data": [
        "security/odental_referral_security.xml",
        "security/ir.model.access.csv",
        "data/odental_referral_sequence.xml",
        "data/odental_referral_cron.xml",
        "wizard/referral_credentials_views.xml",
        "views/referral_views.xml",
        "views/clinical_record_views.xml",
        "views/portal_templates.xml",
        "views/odental_referral_menus.xml",
    ],
    "application": False,
    "installable": True,
}

