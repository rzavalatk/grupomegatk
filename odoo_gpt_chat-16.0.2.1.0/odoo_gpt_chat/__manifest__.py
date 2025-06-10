# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#################################################################################
# Author      : Terabits Technolab (<https://www.terabits.xyz>)
# Copyright(c): 2021-25
# All Rights Reserved.
#
# This module is copyright property of the author mentioned above.
# You can't redistribute/reshare/recreate it for any purpose.
#
#################################################################################

{
    'name': 'AI Chatbot | ChatGPT Live chat Support with your own data | AI powered chatbot with custom knowledge',
    'version': '16.0.2.1.0',
    'category': 'Website',
    'sequence': 40,
    'author': 'Terabits Technolab',
    'license': 'OPL-1',
    'description': """Whisperchat is an AI-powered search bar and chatbot platform that helps users find answers quickly and easily. 
    It allows businesses to enhance their customer service by building a smart chatbot that can instantly answer visitors' queries.
    With Whisperchat, you can create an account, install the chatbot on your website, and provide answers to common customer questions. 
    The platform also offers features like easy training, data versatility, chatbot customization, effortless integration, and conversation analytics.
    AI website chatbot,
    Dedicated AI chatbot for websites,
    Support agent AI chatbot,
    ChatGPT Support Agent for Your Business,
    Train ChatGPT on Your Website Data,
    AI chatbot builder,
    live chatbot,
    chatgpt website,
    chatgpt odoo,
    odoo AI,
    customer support,    
    """,
    
    'summary': """Whisperchat is an AI-powered search bar and chatbot platform that helps users find answers quickly and easily. 
    It allows businesses to enhance their customer service by building a smart chatbot that can instantly answer visitors' queries.
    With Whisperchat, you can create an account, install the chatbot on your website, and provide answers to common customer questions. 
    The platform also offers features like easy training, data versatility, chatbot customization, effortless integration, and conversation analytics.
    AI website chatbot,
    Dedicated AI chatbot for websites,
    Support agent AI chatbot,
    ChatGPT Support Agent for Your Business,
    Train ChatGPT on Your Website Data,
    AI chatbot builder,
    live chatbot,
    chatgpt website,
    chatgpt odoo,
    odoo AI,
    customer support,
    """,
    
    "price": "00.0",
    "currency": "USD",
    'depends': ['base', 'base_setup', 'web', 'crm'],
    'data': [
        'security/res_groups.xml',
	'views/res_users_views.xml',
        'datas/user.xml',
        'views/settings_whisper_patch.xml',
        'views/crm_lead_view.xml',
    ],
    'installable': True,
    'application': True,
    'website': 'https://www.whisperchat.ai',
    'images': ['static/description/banner.gif'],
    'live_test_url': 'https://www.whisperchat.ai/demo',
     'assets': {
        'web.assets_frontend': [
            '/odoo_gpt_chat/static/src/notificationPatch.js',
        ],
        'web.assets_backend': [
            '/odoo_gpt_chat/static/src/notificationPatch.js',
        ]
     }
}
