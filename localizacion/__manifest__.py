{
    'name': 'Localizacion',
    'version': '1.0',
    'description': 'Modulo de localizacion de repartidores',
    'summary': 'Modulo de localizacion de repartidores',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/localizacion_view.xml',  
        'views/main_menu.xml',
    ],
    'assets' : {
        'web.assets_backend': [
            '/localizacion/static/src/xml/localizacion_menu_template.xml',
            '/localizacion/static/src/js/localizacion_menu_action.js',
        ], 
        'web.assets_frontend': [
            '/localizacion/static/src/lib/leaflet.js',
            '/localizacion/static/src/lib/leaflet.css',
        ], 
    },
    'auto_install': False,
    'application': True,
    'installable': True,
}