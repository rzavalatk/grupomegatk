# -*- coding: utf-8 -*-
##############################################################################

{
    'name': "Facturación Electrónica Honduras-2024",
    'summary': """
        Regulación del SAR para regimene de facturación para autoimpresores
        """,
    'description': """
         Regulación del SAR para regimene de facturación para autoimpresores
    """,
    'author': 'Romel Zavala',
    'version': '1.0',
    'license': 'Other proprietary',
    'maintainer': '',
    'contributors': '',
    'category': 'Extra Tools',
    'depends': ['base'],
    'data': [
        'views/account_invoice_view.xml',
        'views/config_authorization_code_view.xml',
        'views/config_journal_view.xml',
        'views/ir_sequence_view.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/journal_settings_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
