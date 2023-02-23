# -*- coding: utf-8 -*-
{
    'name': "Comisiones",

    'summary': """
        Modulo para calcular las comisiones de los usuarios del sistema
        """,

    'description': """
        Modulo para calcular las comisiones de los usuarios del sistema
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    'version': '0.1',

    'depends': ['base','account'],

    'data': [
        'security/security.xml',
        'views/account_comisiones_line.xml',
        'views/account_comisiones.xml',
        'views/assets.xml',
        # 'views/journal.xml',
    ],
}