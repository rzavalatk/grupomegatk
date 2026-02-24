# -*- coding: utf-8 -*-
{
    'name': 'HRMS - Anuncios Oficiales',
    'version': '18.0.1.0.0',
    'category': 'Recursos Humanos',
    'summary': """Gestiona Anuncios Oficiales de RRHH""",
    'description': 'Este módulo ayuda a gestionar anuncios oficiales de recursos humanos '
                   'dirigidos a empleados, departamentos o posiciones específicas.',
    'live_test_url': 'https://youtu.be/VPh1A9-jM5Q',
    'author': 'David Zuniga - MegaTK',
    'company': 'MegaTK',
    'maintainer': 'MegaTK',
    'website': " https://megatk.com",
    'depends': ['hr', 'mail'],
    'data': [
        'security/hr_announcement_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',
        'views/hr_announcement_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_reward_warning_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
