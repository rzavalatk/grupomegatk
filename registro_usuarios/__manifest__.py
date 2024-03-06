# -*- coding: utf-8 -*-
{
    'name': "Registro controlado de usuarios",

    'summary': """
        El registro de usuarios de portal en este modulo se restringen a la website
        de donde se esta registrando
        """,

    'description': """
        El registro de usuarios de portal en este modulo se restringen a la website
        de donde se esta registrando
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Usuarios',
    'version': '0.1',
    "license": "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}