# -*- coding: utf-8 -*-
##############################################################################
##############################################################################

{
    'name': "Lista de Precios Megatk",
    'summary': """
        Módulo de gestion de lsta de precios y configuraciones de pedidos de ventas
        """,
    'description': """
         Módulo de gestion de lsta de precios y configuraciones de pedidos de ventas
    """,
    'author': 'César Alejandro Rodriguez.',
    'version': '1.0',
    'maintainer': '',
    'contributors': '',
    'category': 'Extra Tools',
    'depends': ['base', 'sale', "product"],
    'data': [
        "security/groups.xml",
        'security/ir.model.access.csv',
        "wizard/import_pricelist_view.xml",
        "views/lista_precios_view.xml",
        "views/sale_descuento.xml",
        "views/invoice_price_list.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
