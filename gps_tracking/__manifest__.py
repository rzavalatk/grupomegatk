{
    'name': 'Rastreo GPS',
    'version': '1.0',
    'description': 'Modulo para rastreo GPS',
    'summary': 'Modulo para rastreo GPS',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base','web'
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
            '/gps_tracking/static/src/xml/leaflet_map.xml',
            '/gps_tracking/static/src/js/leaflet_trip_map.js',
            '/gps_tracking/static/lib/leaflet/leaflet.css',
            '/gps_tracking/static/lib/leaflet/leaflet.js',
        ],
    },
    'auto_install': False,
    'application': True,
    'installable': True
}