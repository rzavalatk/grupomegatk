# -*- coding: utf-8 -*-

{
    "name": "PixelPay Payment Acquirer",
    "category": "Accounting/Payment Acquirer",
    "version": "1.8.0-beta.2",
    "description": """PixelPay Payment Acquirer""",
    "author": "PixelPay",
    "website": "https://pixel.hn/",
    "depends": ["payment"],
    "license": "LGPL-3",
    "data": [
        # "security/ir.model.access.csv",
        "views/payment_pixel_templates.xml",
        "views/payment_acquirer.xml",
        "views/res_country_state.xml",
        "data/payment_pixelpay_data.xml",
        "views/payment_template.xml",

    ],
    'external_dependencies': {
        'python': ['pycountry'],
    },
    'odoo-apps': True,
    'images': [
        'static/description/banner_screenshot.gif',
        'static/description/icon.png'
        ],
    'assets': {
        'web.assets_frontend': [
            'https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/aes.min.js',
            'payment_pixelpay/static/src/js/payment_form.js',
        ],
    },

}
