# -*- coding: utf-8 -*-
{
    'name': "Modulo con acciones automatizadas",

    'summary': """
        Maneja la mayoria de acciones automatizadas de Megatk
        """,

    'description': """
        Maneja la mayoria de acciones automatizadas de Megatk
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    'version': '0.1',
    'depends': ['base','account'],
    'data': [
        'views/view.xml',
        'views/cierre_diario.xml',
        'views/email_template.xml'
    ]
}