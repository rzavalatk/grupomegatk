# -*- coding: utf-8 -*-
{
    'name': "Formatos papel para reportes ",

    'summary': """
        formatos para (Facturas, Cotizaciones, Orden de Compra, Orden de entrega, etc.)""",

    'author': "Romel Zavala",
    'website': "https://www.megatk.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','purchase','account','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'reports/formatos_papel.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
}