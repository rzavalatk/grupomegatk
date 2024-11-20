# -*- coding: utf-8 -*-

{
    "name": "Odoo rest API",
    "description": """Rest API para Odoo 16""",
    "summary": """Esta app interactuca con el backend de odoo.""",
    "category": "Tools",
    "version": "16.0.1.0.0",
    'author': 'David Zuniga',
    'company': 'Megatk',
    'maintainer': 'Megatk',  
    "depends": ['base', 'web'],
    "data": [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/connection_api_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
