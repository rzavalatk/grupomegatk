{
    "name": "O Dental Inventario Clínico",
    "summary": "Protocolos de materiales, lotes, vencimientos y consumos por cita",
    "version": "18.0.1.0.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_treatment", "stock", "product_expiry"],
    "data": [
        "security/odental_inventory_security.xml",
        "security/ir.model.access.csv",
        "data/odental_inventory_sequence.xml",
        "views/organization_views.xml",
        "views/service_views.xml",
        "views/material_consumption_views.xml",
        "views/appointment_views.xml",
        "views/stock_picking_views.xml",
        "views/odental_inventory_menus.xml",
    ],
    "application": False,
    "installable": True,
}

