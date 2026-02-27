# -*- coding: utf-8 -*-
{
    'name': 'HRMS - Gestión de Renuncias',
    'version': '18.0.1.0.0',
    'category': 'Recursos Humanos',
    'summary': 'Gestiona el proceso de renuncia de los empleados',
    'description': """Este módulo ayuda a crear y aprobar/rechazar solicitudes
     de renuncia de empleados, incluyendo períodos de preaviso y gestión
     de contratos.""",
    'author': 'David Zuniga - MegaTK',
    'company': 'MegaTK',
    'maintainer': 'MegaTK',
    'website': 'https://www.megatk.com',
    'depends': ['hr_employee_updation'],
    'data': [
        'security/hr_resignation_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_views.xml',
        'views/hr_resignation_views.xml',
    ],
    'live_test_url': 'https://youtu.be/BorJthxY_VI',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
