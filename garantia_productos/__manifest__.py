# -*- coding: utf-8 -*-
{
    'name': "Carta de Garantia",

    'summary': """
        Modulo para Agregar la Garantia al producto entregado en bodega
        """,

    'description': """
        Modulo para Agregar la Garantia al producto entregado en bodega
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    'version': '18.0',
    "license": "LGPL-3",

    'depends': ['base','stock'],

    'data': [
        'views/reports/letter_warrenty.xml',
        'views/stock_picking.xml',
        'views/company.xml',
    ],
}