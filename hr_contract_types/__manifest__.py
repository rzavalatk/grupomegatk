# -*- coding: utf-8 -*-

{
    'name': 'Odoo18 Tipos de contratos para empleados',
    'version': '18.0.1.1.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """
        Tipos de contratos para empleados
    """,
    'description': """Odoo18 Tipos de Contratos de Empleados,Odoo18 Empleado, Contratos de Empleados, Odoo 18""",
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