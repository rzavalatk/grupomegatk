# -*- coding: utf-8 -*-
{
    'name': "Restringir Vendedor",

    'summary': """
        Restringe accesos menores al vendedor en el sistema
        """,

    'description': """
        Restringe accesos menores al vendedor en el sistema

    """,
    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    "license": "LGPL-3",
    'version': '0.1',
    'depends': ['base','crm','sale'],
    'data': [
        # 'security/security.xml',
        'views/res_users.xml',
        'views/account_analitic.xml',
    ],
}