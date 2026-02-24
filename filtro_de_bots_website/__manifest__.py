##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
{
    'name': 'Visitantes reales y descatar bots',
    'summary': 'Improving Website Visitor Tracking: Distinguishing'
               ' High-Quality Visitors from Bots',
    'author': "lumitec GmbH",
    'website': "https://www.lumitec.solutions",
    'category': 'Website',
    'version': '18.0',
    'license': 'OPL-1',
    'images': ['static/description/thumbnail.png'],
    'depends': [
        'base',
        'website_sale',
        'website'
    ],
    'data': [
        'data/defaults.xml',
        'data/cron.xml',
        'views/website_visitor_views.xml'
    ],
    "assets": {
        "web.assets_frontend": [
            "/lt_bot_filter/static/src/js/scroll_event.js",
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
