{
    "name": "O Dental Laboratorio",
    "summary": "Casos de laboratorio, trazabilidad, retrabajos y compras",
    "version": "18.0.1.0.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_inventory", "purchase_stock"],
    "data": [
        "security/odental_laboratory_security.xml",
        "security/ir.model.access.csv",
        "data/odental_laboratory_sequence.xml",
        "views/laboratory_views.xml",
        "views/lab_case_views.xml",
        "views/clinical_record_views.xml",
        "views/purchase_order_views.xml",
        "views/odental_laboratory_menus.xml",
    ],
    "application": False,
    "installable": True,
}

