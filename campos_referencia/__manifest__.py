# -*- coding: utf-8 -*-

{
    'name': "Campos referenciales",

    'summary': """Campos de referencia de localidad y pertenencia de empresa""",

    'description': """
        Campos de referencia de localidad y pertenencia de empresa
    """,

    'author': "Romel Leonel Zavala",
    'website': "http://megaktk.net",

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
        "views/res_users_view.xml"
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'auto_install': False,
}
