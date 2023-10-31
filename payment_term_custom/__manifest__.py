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
    'category': 'Usuarios',
    'version': '0.1',

    'depends': ['base','account','sale'],

    'data': [
        
        'views/account_payment_term.xml',
    ],
}