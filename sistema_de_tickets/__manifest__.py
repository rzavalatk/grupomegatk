# -*- coding: utf-8 -*-
{
    'name': "Sistema de generador de tickets para sorteos",

    'summary': """
        Modulo que genera tickets por compra para futuros sorteos
        """,

    'description': """
        Modulo que genera tickets por compra para futuros sorteos

    """,
    'author': "David Zuniga",
    'website': "dalzubri-netlify.app",
    'category': 'Aplicaciones',
    'version': '0.1',
    "license": "LGPL-3",
    'depends': ['base'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/session_data.xml',
        'views/sorteo_ticket_view.xml',
        'views/sorteo_sorteo_view.xml',
        'views/fechas_festivas_view.xml',
        'views/products_view.xml',
        'views/marcas_view.xml',
        
    ],
    'installable': True,
    'auto_install': False,
}