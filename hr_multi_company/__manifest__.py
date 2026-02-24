# -*- coding: utf-8 -*-
{
    'name': 'Open HRMS - Multi-Compañía',
    'version': '18.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """Habilita Multi-Compañía""",
    'description': 'Este módulo habilita características multi-compañía',
    'author': 'dAVID zUNIGA - MegaTK',
    'company': 'David Zuniga - MegaTK',
    'maintainer': 'David Zuniga - MegaTK',
    'website': "https://www.megatk.com",
    'depends': ['hr', 'hr_contract',
                'hr_expense', 'hr_attendance', 'hr_employee_transfer'],
    'data': [
        'security/multi_company_security.xml',
        'views/hr_attendance_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
