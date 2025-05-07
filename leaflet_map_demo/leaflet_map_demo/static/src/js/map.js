odoo.define('leaflet_map_demo.map', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const LeafletMap = AbstractAction.extend({
        template: 'leaflet_test_template',
        start: function () {
            console.log("Leaflet JS cargado");
            const map = L.map('leaflet_map').setView([51.505, -0.09], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            L.marker([51.505, -0.09]).addTo(map)
                .bindPopup('Aquí estamos.')
                .openPopup();
        },
    });

    core.action_registry.add('leaflet_demo', LeafletMap);
    return LeafletMap;
});