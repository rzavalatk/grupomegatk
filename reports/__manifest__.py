{
    'name': 'Control de reportes',
    'version': '18.0',
    'description': 'Modulo para control de reportes',
    'summary': 'Modulo para control de reportes e imprimirlos',
    'author': 'David Zuniga',
    'license': 'LGPL-3',
    'category': 'reports',
    'depends': [
        'base'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/main_menu_view.xml',
        'views/stock_historial_view.xml',
        'views/customer_purchase_report.xml',
        'views/sistema_puntaje_spt_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'reports/static/src/js/stock_historial.js',
        ],
    },
    'auto_install': False,
    'installable': True,
    'application': True,
    
}