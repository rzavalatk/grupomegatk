# -*- coding: utf-8 -*-

{
    'name': 'HHRR Adelanto de salario',
    'version': '16.0.1.0.0',
    'summary': 'Advance Salary In HR',
    'description': """
        Helps you to manage Advance Salary Request of your company's staff.
        """,
    'category': 'Generic Modules/Human Resources',
    'live_test_url': 'https://youtu.be/5OfoXRZ3AAY',
    'author': "Cybrosys Techno Solutions,Open HRMS",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': [
        'hr_payroll_community', 'hr', 'account', 'hr_contract', 'ohrms_loan',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/salary_structure.xml',
        'views/salary_advance.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

