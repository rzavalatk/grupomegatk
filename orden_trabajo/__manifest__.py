# -*- coding: utf-8 -*-
{
    "name": "Orden de trabajo sale order",
    "author": "Romel Zavala",
    "description": "Orden de Trabajo",
    "category": "Uncategorized",
    "depends": ["base",
        "base_import",
        "sale",
        "account",
      ],
    # always loaded
    'data': [
        'security/groups.xml',
        'views/sale_order_views.xml',
        'reports/external_layout_standard_ot.xml',
        'reports/external_layout_ot.xml',
        'reports/ot_sale_order.xml',
        'reports/orden_trabajo_print_view.xml',
        ],
    "auto_install": False,
    "installable": True,
}