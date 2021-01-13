# -*- coding: utf-8 -*-
{
    'name': "Financiera",

    'description': """
        calculo de prestamos y financiamiento
    """,

    'author': "Romel Zavala",
    'website': "https://megatk.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','banks','payment'],

    # always loaded
    'data': [
        "security/groups.xml",
        'security/ir.model.access.csv',
        "wizard/wizard_recibir_pago.xml",
        "wizard/wizard_generar_cheque.xml",
        "wizard/wizard_generar_cheque_afiliado.xml",
        'wizard/wizard_generar_deposito.xml',
        'wizard/wizard_generar_interes.xml',
        'wizard/wizard_generar_interes_prestamo.xml',
        'views/res_config_settings_views.xml',
        'views/prestamo_views.xml',
        'views/afiliados_views.xml',

        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
}