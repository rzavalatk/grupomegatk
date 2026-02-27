# -*- coding: utf-8 -*-
{
    'name': 'Open HRMS - Empleados desde Usuario',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Crea automáticamente empleados al crear usuarios',
    'description': "Este módulo facilita la creación automática de "
                   "registros de empleados cuando se crean usuarios.",
    'author': 'David Zuniga - MegaTK',
    'company': 'David Zuniga - MegaTK',
    'maintainer': 'David Zuniga - MegaTK',
    'website': 'https://www.megatk.com',
    'depends': ['hr'],
    'data': [
        'views/res_users_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
