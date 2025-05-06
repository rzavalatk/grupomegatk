{
    'name': 'Rastreo GPS',
    'version': '1.0',
    'description': 'Modulo para rastreo GPS',
    'summary': 'Modulo para rastreo GPS',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/gps_tracking_trip_view.xml',
        'views/gps_tracking_main_menu.xml',
        'data/cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/gps_tracking/static/src/js/gps_trip_map.js',
            '/gps_tracking/static/src/js/gps_trip_templates.xml',
            'https://unpkg.com/leaflet@1.9.3/dist/leaflet.js',
            'https://unpkg.com/leaflet@1.9.3/dist/leaflet.css',
        ],
    },
    'auto_install': False,
    'application': True,
    'installable': True
}