# -*- coding: utf-8 -*-
{
    'name': "Reportes y plantillas ",

    'summary': """
        Reportes de impresión (Factura,Cotización,Orden de entrega,etc...)""",

    'author': "Romel Zavala",
    'website': "https://www.megatk.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': "12.0.1.0.0",
    "license": "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base','fields_megatk','fields_megatk_stock'],

    # always loaded
    'data': [
        'reports/baecode_products_stickers.xml',
        'reports/reports.xml',
        'reports/factura_custom_print_view.xml',
        'reports/factura_custom_printe_view.xml',
        'reports/factura_pos_custom_print_view.xml',
        'reports/cotizacion_custom_print_view.xml',
        'reports/cotizacion_custom_print_view_printex.xml',
        'reports/purchase_order_custom_print_view.xml',
        'reports/stock_picking_custom_print_view.xml',
        'reports/stock_picking_custom_print_view_pos.xml',
        'reports/cotizacion_custom_proforma_view.xml',
        'wizard/wizard_sign.xml',
        'views/stock.xml',
        'security/groups.xml',
        'security/ir.model.access.csv'
    ],
}