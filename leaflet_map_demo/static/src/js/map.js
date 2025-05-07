odoo.define('leaflet_map_demo.map', function (require) {
    'use strict';

    if (!document.getElementById('mapid')) return;

    document.addEventListener("DOMContentLoaded", function () {
        var map = L.map('mapid').setView([19.4326, -99.1332], 13);  // CDMX

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        L.marker([19.4326, -99.1332]).addTo(map)
            .bindPopup('Ubicación inicial.')
            .openPopup();
    });
});
