{
    'name': 'Control de reportes',
    'version': '1.0',
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
    ],
    'assets': {
        'web.assets_backend': [
            'static/src/js/stock_historial.js',
        ],
    },
    'auto_install': False,
    'installable': True,
    'application': True,
    
}