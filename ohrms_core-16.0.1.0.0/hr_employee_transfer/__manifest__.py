# -*- coding: utf-8 -*-

{
    'name': 'RRHH Transferencias entre compañias',
    'version': '16.0.1.0.1',
    'category': 'Recursos humanos',
    'summary': 'Transferir empleados de una empresa a otra',
    'description': 'Este modulo se usa para transferir empleados de '
                   'una empresa a otra',
    'author': 'Cybrosys Techno solutions,Open HRMS, Ing. David Zuniga',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Megatk',
    'website': 'https://www.megatk.net',
    'depends': ['base', 'hr', 'hr_contract', 'hr_employee_updation',],
    'data': [
        'security/ir.model.access.csv',
        'security/company_security.xml',
        'views/employee_transfer.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
