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
    "license": "LGPL-3",

    'category': 'Crm',
    'version': '0.1',

    'depends': ['base', 'crm', 'fields_megatk'],

    'data': [
        'views/crm_visits.xml',
        'security/security.xml',
    ],
}