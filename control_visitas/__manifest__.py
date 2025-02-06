{
    'name': 'Control de Visitas',
    'version': '1.0',
    'description': 'Modulo para controlar visitas a las diferentes sucursales',
    'summary': 'Modulo para controlar visitas',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/control_visitas_view.xml',
        'views/main_menu.xml',   
    ],
    'assets': {
        'web.assets_backend': [
            '/control_visitas/static/src/xml/visitas_menu_template.xml',
            '/control_visitas/static/src/js/vistas_menu_action.js',
        ],
    },
    'auto_install': False,
    'application': True,
    'installable': True
}