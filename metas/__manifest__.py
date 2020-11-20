# -*- coding: utf-8 -*-
{
    'name': "Metas Megatk",

    'summary': """
        Asignación de metas al personal del GRUPOMEGA""",

    'description': """
        Asignación de metas al personal del GRUPOMEGA
    """,

    'author': "Romel Zavala",
    'website': "https://megatk.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','fields_megatk'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/hr_employee_equipo_metas.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}