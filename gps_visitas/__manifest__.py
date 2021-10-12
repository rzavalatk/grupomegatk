# -*- coding: utf-8 -*-
{
    'name': "Visitas",

    'summary': """
        Manejo de visitas para vendedores
        """,

    'description': """
        Manejo de visitas para vendedores
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@mehatk.com",

    'category': 'Users',
    'version': '0.1',

    'depends': ['base', 'crm'],

    'data': [
        'views/crm_stage.xml',
        'views/crm_lead.xml',
        'views/crm_visits.xml',
        'security/security.xml',
    ],
}