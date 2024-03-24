# -*- coding: utf-8 -*-
{
    'name': "Módulo de Tesoreria y Caja",
    'summary': """
        Módulo de Gestión de Bancos Multicompañia
        """,
    'description': """
        Gestión de banco y caja
    """,
    'author': "César Alejandro Rodriguez Castillo",
    'category': 'Accounting',
    "license": "LGPL-3",
    'version': '0.1',
    'depends': ['base', 'account', 'analytic', 'purchase'],
    'data': [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_plantilla_view.xml",
        "views/factura_proveedor.xml",
        "views/main_menu_view.xml", 
        "wizard/journal_settings_view.xml",
        "views/ir_sequence_view.xml",
        "views/debit_view.xml",
        "views/account.xml",
        "views/banks_transferences_view.xml",
        "views/config_journal_view.xml",
        "views/check_view.xml",
        "views/payment_view.xml",
        "views/account_payment_view.xml",
        "views/plantilla_banks_view.xml",
        "reports/cheqck_paper_format.xml", 
        "reports/check_report.xml",
        "reports/check_print.xml",
        "reports/voucher_print.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
