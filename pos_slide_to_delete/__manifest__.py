# -*- coding: utf-8 -*-
{
    'name': "POS Swipe to delete Items from cart",
    "live_test_url": "https://demo16.odooskillz.com/web?db=pos_slide_to_delete",
    'author': "Odoo Skillz",
    'summary': 'Adds support for deleting order lines in the POS client with a finger touch swipe.',
    'version': '16.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'description':
        """
        Adds support for deleting order lines in the POS client with a finger touch swipe.
        """,

    'support': 'contact@odooskillz.com',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            # Load libraries first
            'pos_slide_to_delete/static/src/js/app/qz-tray.js',
            'pos_slide_to_delete/static/src/js/**/*.js',
            'pos_slide_to_delete/static/src/css/OrderLine.scss',
        ],
    },
    'license': 'LGPL-3',

    "images": ["static/description/thumbnail.jpg"],

}
