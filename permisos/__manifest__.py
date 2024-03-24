# -*- coding: utf-8 -*-
{
    'name': "permisos",

    'summary': """
        Solicitud y aprobacion de permisos, Calculo de vaciones""",

    'description': """
        Solicitud y aprobacion de permisos, Calculo de vaciones""",

    'author': "Romel Zavala",
    'website': "https://www.megatk.net",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        "security/groups.xml",
        'security/ir.model.access.csv',
        "wizard/wizard_solicitar_permiso.xml",
        'views/default_views.xml',
        'views/permisos_views.xml',
        'views/hr_views.xml',
        'views/email_template.xml',
        
    ]
}