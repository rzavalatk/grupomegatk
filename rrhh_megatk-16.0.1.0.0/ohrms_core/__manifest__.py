# -*- coding: utf-8 -*-

{
    'name': 'Open HRMS Core',
    'version': '16.0.1.0.0',
    'summary': """Open HRMS Odoo17, HRMS odoo17, Odoo HR, HR Dashboard, Odoo17 Payroll, HR Management, Odoo Branch, Odoo Loan, Salary Advance, Odoo17,Payroll,Dashboard,Accounting,HR Kit,HR,Odoo Apps""",
    'description': """Openhrms, Main module of Open HRMS, It brings all others into a single module, Payroll, Payroll Accounting,Expense,
                Dashboard, Employees, Employee Document, Resignation, Salary Advance, Loan Management, Gratuity, Service Request, Gosi, WPS Report, Reminder, Multi Company, Shift Management, Employee History,
                Branch Transfer, Employee Appraisal,Biometric Device, Announcements, Insurance Management, Vacation Management,Employee Appreciations, Asset Custody, Employee Checklist, Entry and Exit Checklist, Disciplinary Actions, openhrms, OpenHRMS, hrms, Attrition Rate, Document Expiry, Visa Expiry, Law Suit Management, Employee, Employee Training""",
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'live_test_url': 'https://youtu.be/kBBlUFofCTs',
    'website': "https://www.openhrms.com",
    'depends': [
        'base', 'web', 'mail',
        'hr',
        'hr_gamification',
        'hr_employee_updation',
        'hr_recruitment',
        'hr_attendance',
        'hr_holidays',
        'hr_payroll_community',
        #'hr_expense',
        'hr_timesheet',
        'oh_employee_documents_expiry',
        'hr_multi_company',
        'ohrms_loan_accounting',
        'ohrms_salary_advance',
        'hr_reward_warning',
        'hrms_dashboard',
        'hr_reminder'
    ],
    "external_dependencies": {"python": ["pandas"]},
    'data': [
        'views/menu_arrangement_view.xml',
        'views/menu_item_form_inherit_view.xml',
    ],
    'assets': {
        'web.assets_backend': [

            'ohrms_core/static/src/css/menu_order_alphabets.css',
            'ohrms_core/static/src/js/appMenu.js',
            'ohrms_core/static/src/js/data.js',
            'ohrms_core/static/src/xml/link_view.xml',
            'ohrms_core/static/templates/side_bar.xml'
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
