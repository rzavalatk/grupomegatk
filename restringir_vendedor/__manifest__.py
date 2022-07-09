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
    'version': '0.1',
    'depends': ['base','crm'],
    'data': [
        # 'security/security.xml',
        'views/res_users.xml',
    ],
}