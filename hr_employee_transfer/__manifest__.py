# -*- coding: utf-8 -*-
{
    'name': 'HRMS - Transferencia de Empleados entre Sucursales',
    'version': '18.0',
    'category': 'Recursos Humanos',
    'summary': 'Transferencia de empleados entre sucursales de la empresa',
    'description': 'Este módulo permite transferir empleados de una sucursal '
                   'a otra, gestionando contratos y registros de manera automática.',
    'author': 'David Zuniga - MegaTK',
    'company': 'MegaTK',
    'maintainer': 'MegaTK',
    'website': 'https://megatk.com',
    'depends': ['hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_employee_security.xml',
        'views/employee_transfer_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
