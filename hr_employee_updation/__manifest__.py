# -*- coding: utf-8 -*-
{
    'name': 'Open HRMS - Información de Empleados',
    'version': '18.0',
    'category': 'Human Resources',
    'summary': """Agregando Campos Avanzados en el Maestro de Empleados""",
    'description': 'Este módulo ayuda a agregar más información '
                   'en los registros de empleados.',
    'live_test_url': 'https://youtu.be/eEecchfl-Q4',
    'author': 'David Zuniga - MegaTK',
    'company': 'Megatk',
    'maintainer': 'David Zuniga - MegaTK',
    'website': "https://megatk.com",
    'depends': ['hr', 'mail', 'hr_gamification', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_employee_relation_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_contract_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_employee_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
