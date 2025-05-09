{
    "name": "Leaflet Map in Form",
    "version": "1.0",
    "depends": ["base", "web"],
    "assets": {
        "web.assets_backend": [
            "leaflet_map_form/static/src/js/leaflet_map.js",
            "https://unpkg.com/leaflet@1.9.3/dist/leaflet.css",
            "https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"
        ]
    },
    "data": [
        "views/leaflet_view.xml"
    ],
    "installable": True,
    "application": True
}