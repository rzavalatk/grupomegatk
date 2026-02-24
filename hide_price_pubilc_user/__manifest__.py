# -*- coding: utf-8 -*-
{
    'name': "Ocultar precio",

    'summary': """
        En este modulo se le oculta el precio al usuario publico
        """,

    'description': """
        En este modulo se le oculta el precio al usuario publico
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    "license": "LGPL-3",

    'category': 'Website/eCommerce',
    'version': '18.0',

    'depends': ['base', 'website', 'website_sale'],

    'data': [
        #'views/price.xml',
        'views/views.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}