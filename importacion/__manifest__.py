# -*- coding: utf-8 -*-
{
    'name': "Modulo de importacion megatk",

    'summary': """
        Calculo de Costo real, ponderacion, arancel...""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Romel Zavala",
    'website': "https://megatk.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_stock','fields_megatk','stock'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/importacion_product.xml',
        'views/stock_picking_import.xml',
        'views/importacion_product_gasto.xml',
        'views/product_view.xml',
        
    ],
    # only loaded in demonstration mode
    'application': True,
    
}