{
    "name": "Biométrico Control de Acceso",
    "version": "1.0.0",
    "category": "Security",
    "summary": "Integración de dispositivos biométricos, registro de marcaciones, comandos y ajustes globales.",
    "description": "Módulo para gestión de dispositivos biométricos, marcaciones, comandos y configuraciones de servidor desde Odoo.",
    "author": "Jiovanny Morales",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["base", "web", "mail"],
    "external_dependencies": {
        "python": ["requests"]
    },
    "data": [
        "security/biometric_security.xml",
        "security/ir.model.access.csv",
        "views/biometric_settings_views.xml",
        "views/biometric_device_views.xml",
        "views/biometric_record_views.xml",
        "views/biometric_command_views.xml",
        "views/biometric_menu.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": False
}
