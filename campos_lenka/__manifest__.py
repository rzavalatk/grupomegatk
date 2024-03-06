# -*- coding: utf-8 -*-
{
    'name': "Lenka Campos",

    'summary': """
        Campos adicionales para el funcionamiento de Lenka""",

    'description': """
        Campos adicionales para el funcionamiento de Lenka
    """,

    'author': "Romel Zavala",
    'website': "http://www.megatk.net",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner_view.xml',
    ],
    # only loaded in demonstration mode
}