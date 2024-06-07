# -*- coding: utf-8 -*-

{
    'name': 'Geolocation in HR Attendance',
    'version': '16.0.1.0.0',
    'summary': "The attendance location of the employee",
    'description': "This module helps to identify the checkin/out location of the employee",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_attendance_user_location/static/src/js/my_attendances.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'external_dependencies': {'python': ['geopy']},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
