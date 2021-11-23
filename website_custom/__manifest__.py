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
        'views/assets/assets.xml',
        'views/website/breadcrum_shop.xml',
        'views/website/chat_facebook.xml',
        'views/website/footer.xml',
        'views/website/products_details.xml',
        'views/snippets/carousel.xml',
        'views/snippets/snippets.xml',
        'views/filters/carousel.xml',
        'views/breadcum.xml',
        'views/carousel.xml',
        'views/consultas.xml',
        'views/hide_content.xml',
        'security/security.xml',
        'static/src/xml/logos_base64.xml',

    ],
}