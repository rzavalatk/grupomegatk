
odoo.define('leaflet_map_demo.map', function (require) {
    'use strict';

    console.log("Leaflet JS cargado");

    document.addEventListener('DOMContentLoaded', function () {
        var mapContainer = document.getElementById('leaflet_map');
        if (mapContainer) {
            var map = L.map('leaflet_map').setView([0, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
        }
    });
});
