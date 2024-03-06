# -*- coding: utf-8 -*-
{
    'name': "Grupos de accesos",

    'summary': """
        Modulo para manejar grupos de accesos que no puedan acceder a ciertas 
        funciones de odoo como cambiar responsable
        """,

    'description': """
        Modulo para manejar grupos de accesos
    """,

    'author': "Alejandro Zelaya",
    'contributors': [
        'David Zuniga - dalzubri.netlify.app',
    ],
    'website': "azelaya@megatk.com",
    "license": "LGPL-3",

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