# -*- coding: utf-8 -*-

{
    'name': 'RRHH Información del empleado',
    'version': '16.0.1.0.0',
    'summary': """Agregar campos avanzados en el Maestro de empleados""",
    'description': 'Agregar campos avanzados en el Maestro de empleados',
    'category': 'Recursos humanos',
    'author': 'Cybrosys Techno solutions,Open HRMS, Ing. David Zuniga',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.megatk.net",
    'depends': ['base', 'hr', 'mail', 'hr_gamification', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/hr_notification.xml',
        'views/contract_days_view.xml',
        'views/updation_config.xml',
        'views/hr_employee_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
