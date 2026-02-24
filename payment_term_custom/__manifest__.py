# -*- coding: utf-8 -*-
{
    'name': "Terminos de pago Megatk",

    'summary': """
        Modulo para personalizar los terminos de pago en todos los modulos
        """,

    'description': """
        Modulo para personalizar los terminos de pago en todos los modulos
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    "license": "LGPL-3",
    'category': 'Usuarios',
    'version': '18.0',

    'depends': ['base','account','sale'],

    'data': [
        'security/groups.xml',
        'views/account_payment_term.xml',
    ],
}