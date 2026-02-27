# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name" : "Multi Chatbot Connector",
    "version" : "18.0.0.1",
    "author" : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    "category" : "Website",
    "license": "Other proprietary",
    "depends" : ['website','mass_mailing','im_livechat','website_livechat'],
    'description': """Geminate comes with a feature of connecting multi chatbots under the same roof and instantly auto activates them based on pre-configured settings based on sequence of chatbots for website live chat.""",
    'summary': 'Geminate comes with a feature of connecting multi chatbots under the same roof and instantly auto activates them based on pre-configured settings based on sequence of chatbots for website live chat.',
    'data': [
                'security/ir.model.access.csv',
                'security/security.xml',
                'data/ir_cron.xml',
                'views/template.xml',
                
            ],
    'images':['static/description/multi_chatbot_connector.png'],
    'assets': {
        'web.assets_frontend': [
            'multi_chatbot_connector/static/src/css/style.css',
            'multi_chatbot_connector/static/src/css/jquery-confirm.min.css',
            'multi_chatbot_connector/static/src/js/im_livechat.js',
            'multi_chatbot_connector/static/src/js/jquery-confirm.min.js',
        ],
        'web.assets_backend': [
            'multi_chatbot_connector/static/src/js/composer.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'price': 299.00,
    'currency': 'EUR' 
}
