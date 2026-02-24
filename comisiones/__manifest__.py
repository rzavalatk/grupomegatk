# -*- coding: utf-8 -*-
{
    'name': "Comisiones",

    'summary': """
        Modulo para calcular las comisiones de los usuarios del sistema
        """,

    'description': """
        Modulo para calcular las comisiones de los usuarios del sistema
    """,

    'author': "Alejandro Zelaya / David Zuniga",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    'version': '18.0',

    'depends': ['base','account'],

    'data': [
        'security/security.xml',
        'security/rules.xml',
        'views/account_comisiones_line.xml',
        'views/account_comisiones.xml',
        'views/assets.xml',
        # 'views/journal.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'comisiones/static/src/js/account_comisiones.js',
        ],
    },
}