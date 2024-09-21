
{
    'name': 'Etiquetas para productos',
    'version': '16.0.2.7.2',
    'category': 'Extra Tools',
    'author': 'David Zuniga - dalzubri.netlify.app',
    'website': 'dalzubri.netlify.app',
    'license': 'LGPL-3',
    'summary': 'Imprimir etiquetas de producto personalizadas con código de barras | Etiqueta de producto con código de barras',
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'depends': [
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/product_label_reports.xml',
        'report/product_label_templates.xml',
        'wizard/print_product_label_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'support': 'info@megatk.com',
    'application': True,
    'installable': True,
    'auto_install': False,
}
