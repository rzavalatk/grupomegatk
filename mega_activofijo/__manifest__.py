# -*- coding: utf-8 -*-
{
    'name': "mega_activofijo",

    'summary': """
        personalizacion del modulo de activo fijo""",

    'description': """
        personalizacion del modulo de activo fijo
    """,

    'author': "Romel Zavala",
    'website': "www.megatk.net",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account_asset','hr','product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/acyivo_fijo_view.xml',
    ],
}