# -*- coding: utf-8 -*-
{
    'name': "Ksolves Contact Us Page",

    'summary': """
        Ksolves Contact Us Page""",

    'description': """
        In this Module we load the Contact Us Page for Website.   
    """,

    'author': "Ksolves",
    'website': "http://www.ksolves.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website_crm', 'ks_theme_kinetik'],

    # always loaded
    'data': [
        'views/ks_assets.xml',
        'views/ks_contact_form.xml',
        'views/ks_contact_form_snippet.xml',
    ],
}
