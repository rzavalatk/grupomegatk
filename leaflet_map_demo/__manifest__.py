
{
    'name': 'Leaflet Map Demo',
    'version': '1.0',
    'depends': ['web'],
    'data': [
        'views/map_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/leaflet_map_demo/static/src/js/map.js',
            'https://unpkg.com/leaflet@1.9.3/dist/leaflet.js',
            'https://unpkg.com/leaflet@1.9.3/dist/leaflet.css',
        ],
    },
    'installable': True,
    'application': True,
}
