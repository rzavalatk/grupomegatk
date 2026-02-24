# -*- coding: utf-8 -*-
{
    'name': "Marcaciones y Horas extra",
    'summary': """
        Modulo para manejar marcaciones y horas extra
        """,
    'description': """
        Modulo para manejar marcaciones y horas extra
    """,
    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Empleados',
    "license": "LGPL-3",
    'version': '0.1',
    'depends': ['base','hr'],
    'data': [
        'security/security.xml',
        'wizard/hours_xtra.xml',
        'views/assets.xml',
        'views/employees.xml',
        'views/view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'marcacion_y_horas_extras/static/src/js/controlle.js',
            'marcacion_y_horas_extras/static/src/js/excelxml.js',
        ],
    },
}