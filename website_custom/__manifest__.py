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
    "license": "LGPL-3",
    'depends': ['base','website','banks'],

    'data': [
        'views/assets/assets.xml',
        'views/website/breadcrum_shop.xml',
        'views/website/chat_facebook.xml',
        'views/website/footer.xml',
        'views/website/social_buttons.xml',
        'views/website/products_details.xml',
        'views/snippets/carousel.xml',
        'views/snippets/snippets.xml',
        'views/snippets/video_youtube.xml',
        'views/filters/carousel.xml',
        'views/breadcum.xml',
        'views/res_confog_setting.xml',
        'views/carousel.xml',
        'views/menu_social.xml',
        'views/consultas.xml',
        'views/hide_content.xml',
        'views/video_web.xml',
        'security/security.xml',
        'static/src/xml/logos_base64.xml',
    ],
    'qweb_template_dict': {
        'backend': [
            '',
        ],
        'frontend': [
            '/website_custom/static/src/js/controller.js',
            '/website_custom/static/src/css/styles.css',
            '/website_custom/static/src/js/snippets/carousel.js',
            '/website_custom/static/src/js/snippets/video_web.js',
            ''
        ],
    },
}