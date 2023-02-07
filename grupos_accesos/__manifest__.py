# -*- coding: utf-8 -*-
{
    'name': "Grupos de accesos",

    'summary': """
        Modulo para manejar grupos de accesos
        """,

    'description': """
        Modulo para manejar grupos de accesos
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",

    'category': 'Usuarios',
    'version': '0.1',

    'depends': ['base','sale','account'],

    'data': [
        'security/groups.xml',
        'security/edit_responsable.xml',
        'views/config.xml',
        'views/crm_lead.xml',
    ],
}