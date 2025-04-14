# -*- coding: utf-8 -*-

{
    'name': 'HHRR recordatorios',
    'version': '16.0.2.0.0',
    'category': 'Recursos humanos',
    'summary': 'Recordatorios para campos de fecha que sean de vencimiento',
    'author': 'Cybrosys Techno solutions,Open HRMS, Ing. David Zuniga',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.megatk.net",
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_reminder_security.xml',
        'views/hr_reminder_view.xml',
        'data/ir_cron_reminder.xml'
        
    ],
    'assets': {
        'web.assets_backend': [
            'hr_reminder/static/src/css/notification.css',
            'hr_reminder/static/src/scss/reminder.scss',
            'hr_reminder/static/src/xml/reminder_topbar.xml',
            'hr_reminder/static/src/js/reminder_topbar.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
