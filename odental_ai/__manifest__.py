{
    "name": "O Dental Asistente IA",
    "summary": "Comandos de voz con propuestas, confirmación, ejecución y auditoría",
    "version": "18.0.1.0.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_portal", "web"],
    "data": [
        "security/odental_ai_security.xml",
        "security/ir.model.access.csv",
        "data/odental_ai_sequence.xml",
        "views/ai_session_views.xml",
        "views/ai_audit_views.xml",
        "views/context_views.xml",
        "views/odental_ai_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odental_ai/static/src/js/voice_text_field.js",
            "odental_ai/static/src/xml/voice_text_field.xml",
        ],
    },
    "application": False,
    "installable": True,
}
