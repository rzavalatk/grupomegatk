# -*- coding: utf-8 -*-
{
    'name': "Formatos papel para reportes ",

    'summary': """
        formatos para (Facturas, Cotizaciones, Orden de Compra, Orden de entrega, etc.)""",

    'author': "David Zuniga - MegaTK",
    'website': "https://www.megatk.net",
    'category': 'Studio',
    'version': '18.0',
    "license": "LGPL-3",
    'depends': ['base', 'sale', 'purchase', 'account', 'stock'],
    'data': [
        'reports/formatos_papel.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}