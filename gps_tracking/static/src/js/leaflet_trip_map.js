odoo.define('your_module.LeafletMapWidget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var LeafletMapWidget = AbstractField.extend({
        className: 'o_leaflet_map',
        supportedFieldTypes: ['char'],

        init: function (parent, name, record, options) {
            console.log("1");
            
            this._super.apply(this, arguments);
            this.map = null;
            this.marker = null;
            this._isMounted = false;
        },

        willStart: function () {
            // Cargar Leaflet dinámicamente si no está cargado
            if (!window.L) {
                return $.getScript("https://unpkg.com/leaflet@1.9.3/dist/leaflet.js")
                    .then(function() {
                        $('<link>')
                            .appendTo('head')
                            .attr({
                                type: 'text/css',
                                rel: 'stylesheet',
                                href: 'https://unpkg.com/leaflet@1.9.3/dist/leaflet.css'
                            });
                    });
            }
            return this._super();
        },

        _render: function () {
            if (!this._isMounted) {
                this.$el.html('<div class="leaflet-map-container" style="height: 400px; width: 100%;"></div>');
                this._isMounted = true;
            }

            // Esperar a que el DOM esté listo
            this._super().then(function() {
                if (this.map) {
                    this.map.remove();
                }

                var mapContainer = this.$el.find('.leaflet-map-container')[0];
                this.map = L.map(mapContainer);

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(this.map);

                // Centrar el mapa si hay coordenadas
                if (this.value) {
                    try {
                        var coords = JSON.parse(this.value);
                        if (coords.lat && coords.lng) {
                            this.map.setView([coords.lat, coords.lng], 13);
                            this._addMarker(coords.lat, coords.lng);
                            return;
                        }
                    } catch (e) {
                        console.error("Error parsing coordinates", e);
                    }
                }

                // Vista por defecto
                this.map.setView([51.505, -0.09], 2);

                // Manejador de clics
                this.map.on('click', this._onMapClick.bind(this));
                
                // Forzar redimensionamiento
                setTimeout(this._invalidateSize.bind(this), 0);
            }.bind(this));
        },

        _addMarker: function(lat, lng) {
            if (this.marker) {
                this.map.removeLayer(this.marker);
            }
            this.marker = L.marker([lat, lng]).addTo(this.map);
        },

        _onMapClick: function(e) {
            this._addMarker(e.latlng.lat, e.latlng.lng);
            this._setValue(JSON.stringify({
                lat: e.latlng.lat,
                lng: e.latlng.lng
            }));
        },

        _invalidateSize: function() {
            if (this.map) {
                this.map.invalidateSize();
            }
        },

        destroy: function () {
            if (this.map) {
                this.map.remove();
            }
            this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('leaflet_map', LeafletMapWidget);

    return LeafletMapWidget;
});