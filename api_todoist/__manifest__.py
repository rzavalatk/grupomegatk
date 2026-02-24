# -*- coding: utf-8 -*-
{
    'name': "Integracion de Todoist",

    'summary': """
        Modulo que integra Todoist a Odoo en el modulo del CRM
        """,

    'description': """
        Modulo que integra Todoist a Odoo en el modulo del CRM

    """,
    'author': "Alejandro Zelaya",
    "license": "LGPL-3",
    'website': "azelaya@megatk.com",
    'category': 'Aplicaciones',
    'version': '18.0.0',

    'depends': ['base','crm'],
    'data': [
        'security/security.xml',
        'views/crm_todoist_users.xml',
    ]
}