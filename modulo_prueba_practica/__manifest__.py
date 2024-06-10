# -*- coding: utf-8 -*-

{
    'name': 'practica',
    'depends': [
        'base_setup' 

    ],
    'data': [
        'security/ir.model.access.csv',
        'views/state_property_views.xml',
        'views/state_property_type.xml',
    ],
    'css': ['static/src/css/crm.css'],
    'installable': True,
    'application': True,
    'auto_install': False
}