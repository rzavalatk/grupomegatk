# -*- encoding: utf-8 -*-
{
    "name": "Gestión de gastos Grupo Mega",
    "version": "14",
    "category": "accounting",
    "author": "César Alejandro Rodriguez",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        'banks',
        "analytic",
        "sale",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_generar_cheque.xml",
        "views/gastos_view.xml",
        "views/res_partner_view.xml",
        "views/conceptos_view.xml",
        "views/tarjeta_view.xml",
        #"views/sequence_view.xml",
        #"views/res_users_view.xml"
    ],
    "installable": True,
}
