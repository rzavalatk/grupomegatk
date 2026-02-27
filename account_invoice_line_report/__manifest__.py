# -*- coding: utf-8 -*-
{
    'name': 'Account Invoice Line Report',
    'summary': 'Lineas de facturas validadas ',
    'version': '18.0',
    'category': 'Account',
    "license": "LGPL-3",
    'author': 'David Zuniga',
    'depends': [
        'account', 'fields_megatk',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/account_invoice_report_view.xml',
    ],
    'installable': True,
}
