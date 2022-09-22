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
    'website': "azelaya@megatk.com",
    'category': 'Aplicaciones',
    'version': '0.1',

    'depends': ['base','crm'],
    'data': [
        'security/security.xml',
        'views/crm_todoist_users.xml',
    ]
}