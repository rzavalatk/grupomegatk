# -*- coding: utf-8 -*-
{
    'name': "Admin Website",

    'summary': """
        Módulo para administrar información y multimedia del website
    """,

    'description': """
        Módulo para administrar información y multimedia del website
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'user',
    'version': '0.1',

    'depends': ['base','website'],

    'data': [
        'views/website/breadcrum_shop.xml',
        'views/snippets/carousel.xml',
        'views/snippets/snippets.xml',
        'views/filters/carousel.xml',
        'views/breadcum.xml',
        'views/carousel.xml',
        'security/security.xml',
    ],
}