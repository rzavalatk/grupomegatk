# -*- coding: utf-8 -*-
{
    'name': "Sub modulos para facturacion",

    'summary': """
        Sistema para manejar sub modulos relacionados con el modulo de facturación
        """,

    'description': """
        Sistema para manejar sub modulos relacionados con el modulo de facturación

    """,
    'author': "David Zuniga",
    'website': "dalzubri-netlify.app",
    'category': 'Aplicaciones',
    'version': '18.0',
    "license": "LGPL-3",
    'depends': ['base','account'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/departamento_view.xml',
        'views/ciudad_view.xml',
        'views/type_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}