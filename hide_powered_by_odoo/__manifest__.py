# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hide Powered By Odoo',
    'version': '15.0.1.0.0',
    'sequence': 1,
    'summary': """
        Hide Powered By Odoo login screen
    """,
    'description': "Hide Powered By Odoo in login screen.",
    'author': 'Innoway',
    'maintainer': 'Innoway',
    'price': '0.0',
    'currency': 'USD',
    'website': 'https://innoway-solutions.com',
    'license': 'LGPL-3',
    'images': [
        'static/description/wallpaper.png'     
    ],
    'depends': [
        'web'
    ],
    'data': [
        'views/login_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
