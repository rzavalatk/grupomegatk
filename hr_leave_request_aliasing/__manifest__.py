# -*- coding: utf-8 -*-
{
    'name': 'Open HRMS - Alias de Solicitud de Ausencias',
    'version': '18.0',
    'category': 'Human Resources',
    'summary': """Generación automática de solicitudes de ausencias desde correos entrantes.""",
    'description': """Este módulo simplifica la creación de solicitudes de ausencias al 
     generar solicitudes automáticamente desde correos entrantes, haciendo el proceso 
     eficiente, ahorrando tiempo y mejorando la experiencia del empleado.""",
    'author': 'Cybrosys Techno solutions, Open HRMS, David Zuniga - MegaTK',
    'company': 'Cybrosys Techno Solutions, megaTK',
    'maintainer': 'megaTK',
    'website': "https://www.megatk.com",
    'depends': ['hr_holidays'],
    'data': [
        'data/mail_alias_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
