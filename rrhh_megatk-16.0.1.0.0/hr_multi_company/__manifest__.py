# -*- coding: utf-8 -*-
{
    'name': 'RRHH Multi-Compañia',
    'version': '16.0.1.0.0',
    'summary': """Permite la gestión de múltiples empresas""",
    'description': 'Este módulo habilita funciones para múltiples empresas.',
    'category': 'Recursos humanos',
    'author': 'Cybrosys Techno solutions,Open HRMS, Ing. David Zuniga',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.megatk.net",
    'depends': ['base', 'hr','hr_contract', 'hr_payroll_community', 
                #'hr_expense', 
                'hr_attendance', 'hr_employee_transfer'],
    'data': [
        'views/hr_company_view.xml',
        'views/multi_company_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
