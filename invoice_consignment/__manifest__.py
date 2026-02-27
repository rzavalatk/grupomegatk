# -*- coding: utf-8 -*-
{
    'name': "Facturas de consignación",

    'summary': """
        Modulo para crear facturas temporales de consignación
        """,

    'description': """
        Modulo para crear facturas temporales de consignación
    """,

    'author': "David Zuniga",
    'website': "dzuniga@megatk.com",
    "license": "LGPL-3",
    'category': 'Usuarios',
    'version': '18.0',
    'depends': ['base','account','sale'],
    'data': [
        'views/account_invoice.xml',
        'views/sale_wizar_invoice.xml',
        'views/inherit_action_invoice.xml',
        'views/type_account.xml',
        'views/res_config.xml',
    ],
}