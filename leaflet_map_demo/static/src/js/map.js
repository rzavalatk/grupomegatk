// static/src/js/mapa.js
odoo.define('tu_modulo.LeafletMap', function (require) {
    "use strict";
    
    var Widget = require('web.Widget');
    
    var LeafletMap = Widget.extend({
        template: 'leaflet_map_demo.leaflet_map',
        
        start: function () {
            this._super.apply(this, arguments);
            
            // Inicializar el mapa después de que el DOM esté listo
            this._initMap();
        },
        
        _initMap: function () {
            // Crear el mapa
            this.map = L.map(this.$el[0]).setView([51.505, -0.09], 13);
            
            // Añadir capa de tiles (OpenStreetMap por defecto)
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.map);
            
            // Añadir un marcador
            L.marker([51.5, -0.09]).addTo(this.map)
                .bindPopup('Ubicación de ejemplo')
                .openPopup();
        }
    });
    
    return LeafletMap;
});