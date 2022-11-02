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
        # 'views/cierre_diario_cron.xml',
        'wizard/wizard.xml',
        'security/security.xml',
        'views/cierre.xml',
        'views/cierre_line.xml',
        'views/email_template.xml',
        'views/res_config.xml',
    ]
}