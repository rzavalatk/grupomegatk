# -*- coding: utf-8 -*-
{
    'name': "Modulo con acciones automatizadas",

    'summary': """
        Maneja la mayoria de acciones automatizadas de Megatk
        """,

    'description': """
        Maneja la mayoria de acciones automatizadas de Megatk
    """,

    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'Usuarios',
    'version': '0.1',
    'depends': ['base','account','fields_megatk'],
    'data': [
        'wizard/wizard.xml',
        'security/security.xml',
        'security/rules.xml',
        #'views/account_invoice.xml',
        'views/cierre_diario_cron.xml',
        #'views/invoice_expire_cron.xml',
        #'views/product_expired_cron.xml',
        'views/report_marca_cron.xml',
        'views/cierre.xml',
        'views/order_point.xml',
        #'views/invoice_expire.xml',
        'views/cierre_cxc.xml',
        'views/product_report.xml',
        'views/cierre_line.xml',
        'views/email_template.xml',
        'views/email_template_2.xml',
        'views/stock_production_lot.xml',
        'views/res_config.xml',
    ]
}