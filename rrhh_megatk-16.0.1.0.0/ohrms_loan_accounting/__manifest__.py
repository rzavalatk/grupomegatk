# -*- coding: utf-8 -*-

{
    'name': 'HHRR Contabilidad de préstamos',
    'version': '16.0.1.0.0',
    'summary': 'Open HRMS Loan Accounting',
    'description': """
        Create accounting entries for loan requests.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "Cybrosys Techno Solutions,Open HRMS",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'live_test_url': 'https://youtu.be/NFZfiHyn0-0',
    'website': "https://www.openhrms.com",
    'depends': [
        'base', 'hr_payroll_community', 'hr', 'account', 'ohrms_loan',
    ],
    'data': [
        'views/hr_loan_config.xml',
        'views/hr_loan_acc.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
