# -*- coding: utf-8 -*-

{
    'name': 'Odoo16 Tipos de contratos para empleados',
    'version': '16.0.1.1.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """
        Tipos de contratos para empleados
    """,
    'description': """Odoo16 Tipos de Contratos de Empleados,Odoo16 Empleado, Contratos de Empleados, Odoo 16""",
    'author': 'Megatk',
    'company': 'Megatk',
    'maintainer': 'Megatk',
    'depends': ['hr', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_view.xml',
        'data/hr_contract_type_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}