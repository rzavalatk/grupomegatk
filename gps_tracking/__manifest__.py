{
    'name': 'Rastreo GPS',
    'version': '1.0',
    'description': 'Modulo para rastreo GPS',
    'summary': 'Modulo para rastreo GP',
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
        'views/gps_tracking_map_view.xml',
        'data/ir_sequence.xml',
        'data/cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/gps_tracking/static/lib/leaflet/leaflet.css',
            '/gps_tracking/static/lib/leaflet/leaflet.js',    
            '/gps_tracking/static/lib/leaflet-routing-machine/leaflet-routing-machine.css',    
            '/gps_tracking/static/lib/leaflet-routing-machine/leaflet-routing-machine.js',    
            '/gps_tracking/static/src/js/tracking_map_action.js',
            '/gps_tracking/static/src/js/tracking_menu_action.js',
            '/gps_tracking/static/src/xml/tracking_map_template.xml',
            '/gps_tracking/static/src/xml/tracking_menu_template.xml',
        ],
    },
    'auto_install': False,
    'application': True,
    'installable': True
}