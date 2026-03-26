# -*- coding: utf-8 -*-
{
    'name': 'BAC Payment Control',
    'summary': 'Control basico de links BAC y pagos duplicados por pedido',
    'description': '''
Modulo de prueba para configurar links BAC fijos por producto y llevar
un control manual de pagos y duplicados desde pedidos de venta.
    ''',
    'author': 'GitHub Copilot',
    'website': 'https://github.com',
    'category': 'Sales',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/bac_payment_control_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}