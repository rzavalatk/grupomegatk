# -*- coding: utf-8 -*-
{
    'name': "Campos Actualizacion company",

    'summary': """Campos de referencia de localidad y pertenencia de empresa""",

    'description': """
        Campos de referencia de localidad y pertenencia de empresa
    """,

    'author': "Romel Leonel Zavala",
    'website': "http://megaktk.net",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    'data': [
        'views/res_company.xml',
    ],

    # always loaded
   
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'auto_install': False,
}