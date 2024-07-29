# -*- coding: utf-8 -*-
{
    'name': 'Loan Management',
    'version': '16.0.1.0.0',
    'summary': 'Helps You To Manage Loan Requests/Disbursement/'
               'Repayments/Amortization Operations',
    'description': 'Module Allows To Create different types of loans,'
                   'Manage Loan Requests And Amortization Operations Simply,'
                   'Create Invoices For Each Repayment Amounts',
    'category': 'Accounting',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'account', 'base', 'l10n_generic_coa'],
    'data': [
        'security/loan_management_groups.xml',
        'security/loan_management_security.xml',
        'security/ir.model.access.csv',
        'data/secuencia.xml',
        'views/loan_type_views.xml',
        'views/loan_request_views.xml',
        'views/repayment_lines_views.xml',
        'views/loan_documents_views.xml',
        'views/res_config_settings_views.xml',
        'views/loan_management_menus.xml',
        'views/res_partner_views.xml',
        'wizard/message_popup_views.xml',
        'wizard/reject_reason_views.xml',
        'report/loan_management_reports.xml',
        'report/loan_report_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
