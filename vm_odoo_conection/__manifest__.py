# -*- coding: utf-8 -*-
{
    'name': "Maquina expendedora",
    'summary': """
        Módulo de conexion con app de vending machine
        """,
    'description': """
        conexion entre odoo y app de vm
    """,
    'author': "Jiovanny Francisco Morales Hernandez",
    "license": "LGPL-3",
    'version': '0.1',
    'depends': ['base', 'hr'],
    'data': [
        "security/ir.model.access.csv",
        "views/attr_employee_views.xml",
        "views/transaccion_report.xml"
        "wizard/wizard.xml",
        "data/cron.xml"

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
