# -*- coding: utf-8 -*-
{
    'name': "Modulo de importacion megatk",
    'summary': """
        Calculo de Costo real, ponderacion, arancel...""",
    'description': """
        Long description of module's purpose
    """,
    'author': "David Zuniga - MegaTK",
    'website': "https://megatk.net",
    'category': 'Uncategorized',
    'version': '18.0',
    "license": "LGPL-3",
    'depends': ['base','purchase_stock','fields_megatk','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/importacion_product.xml',
        'views/stock_picking_import.xml',
        'views/importacion_product_gasto.xml',
        'views/product_view.xml',
    ],
    'application': True,
    
}