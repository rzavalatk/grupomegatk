# -*- coding: utf-8 -*-
{
    'name': "Conciliación bancaria",
    'summary': """
        Módulo de Conciliación bancaria 
        """,
    'description': """
        Bancos y conciliación
    """,
    'author': "César Alejandro Rodriguez Castillo",
    'category': 'Banking',
    'version': '0.1',
    'depends': ['base', 'account', 'banks', 'fields_megatk_stock'],
    'data': [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_generar_movimiento.xml",
        "views/conciliacion_view.xml", 
        "reports/conciliacion_print.xml",
        "reports/conciliacion_print_view.xml",
        "reports/no_conciliacion_print.xml",
        "reports/unconciliacion_print_view.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
