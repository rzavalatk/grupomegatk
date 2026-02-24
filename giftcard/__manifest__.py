# -*- coding: utf-8 -*-
{
    'name': "Gift Card",

    'summary': """
        Creacion y validacion de Gift Card""",

    'description': """
        Creacion y validacion de Gift Card
    """,

    'author': "Romel Zavala",
    'website': "http://www.yourcompany.com",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

     'data': [
        'reports/giftcard_report.xml',
        'reports/external_layout_standard_giftcard.xml',
        'reports/giftcard_print_view.xml',
        'reports/voucher_report_view.xml',
        'data/giftcard_data.xml',
        "security/groups.xml",
        'security/ir.model.access.csv',
        'wizard/wizard_giftcard_cobrar.xml',
        'wizard/wizard_giftcard_recar.xml',
        'views/gifcard_views.xml',
    ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
}