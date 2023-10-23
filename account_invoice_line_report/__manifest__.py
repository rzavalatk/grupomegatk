# -*- coding: utf-8 -*-
{
    'name': 'Account Invoice Line Report',
    'summary': 'Lineas de facturas validadas ',
    'version': '12.0',
    'category': 'Account',
    'author': 'Romel Zavala',
    'depends': [
        'account', 'fields_megatk',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/account_invoice_report_view.xml',
    ],
    'installable': True,
}
