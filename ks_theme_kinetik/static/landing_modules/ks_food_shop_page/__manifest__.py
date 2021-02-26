# -*- coding: utf-8 -*-
{
    'name': "Food Shop Landing Page",

    'summary': """
        Food Shop Landing Page""",

    'description': """
        In this Module we load the Food Shop Landing Page.   
    """,

    'author': "Ksolves",
    'website': "http://www.ksolves.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'website'],

    # always loaded
    'data': [
        'views/ks_landing_snippets.xml',
        'views/ks_food_shop_page.xml',
        'data/ks_demo_data.xml',


    ],
}
