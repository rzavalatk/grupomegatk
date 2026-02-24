# -*- coding: utf-8 -*-
{
    'name': "Firmar ordenes",

    'summary': """
        Modulo filtra las ordenes que faltan por firmar
        """,

    'description': """
        Modulo filtra las ordenes que aun no se han firmado,
        ayudando al usuario a ver que ordenes estan pendientes
        por autorizar.
        """,

    'author': "Alejandro Zelaya",
    'website': "www.megatk.com",
    'category': 'Usuarios',
    'version': '18.0.1.0.0',
    "license": "LGPL-3",
    'depends': ['base', 'stock'],
    'data': [
        'security/security.xml',
        'views/view.xml',
        'views/action.xml',
        'data/cron.xml',
    ],
}
