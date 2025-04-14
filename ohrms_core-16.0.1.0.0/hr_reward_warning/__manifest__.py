# -*- coding: utf-8 -*-

{
    'name': 'RRHH Comunicados Oficiales',
    'version': '16.0.1.0.0',
    'summary': """Gestor de comunicados para empleados de la empresa""",
    'description': 'ESte modulo ayuda a la gestión de comunicados o anuncios para los empleados',
    'category': 'Recursos humanos',
    'author': 'Cybrosys Techno solutions,Open HRMS, Ing. David Zuniga',
    'company': 'Megatk',
    'website': "https://www.megatk.net",
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/reward_security.xml',
        'views/hr_announcement_view.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
