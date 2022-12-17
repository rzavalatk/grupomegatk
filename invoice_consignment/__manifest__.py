# -*- coding: utf-8 -*-
{
    'name': "Facturas de consignación",

    'summary': """
        Modulo para crear facturas temporales de consignación
        """,

    'description': """
        Modulo para crear facturas temporales de consignación
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    'version': '0.1',
    'depends': ['base','account','sale'],
    'data': [
        'views/account_invoice.xml',
        'views/sale_wizar_invoice.xml',
        'views/inherit_action_invoice.xml',
        'views/res_config.xml',
    ],
}