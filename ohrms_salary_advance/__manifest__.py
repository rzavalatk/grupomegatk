# -*- coding: utf-8 -*-
{
    'name': 'Open HRMS - Adelanto de Salario',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Adelanto de Salario en Open HRMS',
    'description': """Este módulo es un componente de la suite Open HRMS. 
     Ayuda al usuario a gestionar solicitudes de adelanto de salario de empleados. 
     Puede configurar reglas de adelanto de salario, establecer límite de adelanto, 
     número mínimo de días y proporcionar adelanto de salario a los empleados.""",
    'live_test_url': 'https://youtu.be/5OfoXRZ3AAY',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['hr', 'account',
                'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'security/salary_advance_security.xml',
        'data/ir_sequence_data.xml',
        'views/salary_advance_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
