# -*- coding: utf-8 -*-
##############################################################################
##############################################################################
{
    'name': 'Gestión de Pago de clientes',
    'version': '10.0.1.0',
    'author': 'César Alejandro Rodriguez',
    'company': 'Honduras Open Spurce',
    'category': 'Accounting',
    'summary': 'Pagos de clientes',
    'description': """ Pagos de clientes """,
    "depends": [
        "base",
        "account",
        "mail",
    ],
    'data': [
        "security/groups.xml",
        'security/ir.model.access.csv',
        'data/account_pdc_data.xml',
        'views/account_payment_view.xml',
    ],
    'images': ['static/description/pdc_banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
