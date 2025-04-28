# -*- coding: utf-8 -*-

{
    'name': 'RRHH Renuncias',
    'version': '16.0.1.0.0',
    'summary': 'Proceso de renuncia para empleados de la empresa',
    'author': 'Cybrosys Techno solutions,Open HRMS, Ing. David Zuniga',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.megatk.net',
    'depends': ['hr', 'hr_employee_updation', 'mail'],
    'category': 'Generic Modules/Human Resources',
    'maintainer': 'Megatk',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/resign_employee.xml',
        'views/hr_employee.xml',
        'views/resignation_view.xml',
        'views/approved_resignation.xml',
        'views/resignation_sequence.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
