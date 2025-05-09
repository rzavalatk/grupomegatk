odoo.define('leaflet_map.LeafletWidget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');

    var _t = core._t;

    var LeafletWidget = AbstractField.extend({
        className: 'o_leaflet_widget',
        supportedFieldTypes: ['char'],
        jsLibs: [
            '/leaflet_map/static/src/js/leaflet.js',
            '/leaflet_map/static/src/css/leaflet.css'
        ],

        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            this.map = null;
            this.marker = null;
        },

        willStart: function () {
            // Verificar si Leaflet está cargado
            if (typeof L === 'undefined') {
                return Promise.reject("Leaflet library not loaded");
            }
            return this._super();
        },

        _render: function () {
            this.$el.empty().html('<div class="leaflet-container" style="height: 400px; width: 100%;"></div>');
            
            if (!this.map) {
                this.map = L.map(this.$el.find('.leaflet-container')[0]);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    maxZoom: 19,
                }).addTo(this.map);
            }

            // Centrar el mapa en las coordenadas guardadas o en una ubicación por defecto
            var defaultView = [0, 0];
            var zoomLevel = 2;
            
            if (this.value) {
                try {
                    var coords = JSON.parse(this.value);
                    if (coords.lat && coords.lng) {
                        defaultView = [coords.lat, coords.lng];
                        zoomLevel = 13;
                        if (this.marker) {
                            this.map.removeLayer(this.marker);
                        }
                        this.marker = L.marker(defaultView).addTo(this.map);
                    }
                } catch (e) {
                    console.error(_t("Error parsing coordinates"), e);
                }
            }

            this.map.setView(defaultView, zoomLevel);

            // Manejar clics en el mapa
            this.map.on('click', this._onMapClick.bind(this));

            // Forzar redimensionamiento
            setTimeout(this._invalidateMap.bind(this), 0);
        },

        _onMapClick: function (e) {
            if (this.marker) {
                this.map.removeLayer(this.marker);
            }
            this.marker = L.marker(e.latlng).addTo(this.map);
            this._setValue(JSON.stringify({
                lat: e.latlng.lat,
                lng: e.latlng.lng
            }));
        },

        _invalidateMap: function () {
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

    // Registrar el widget con un nombre único
    fieldRegistry.add('leaflet_map_widget', LeafletWidget);

    return {
        LeafletWidget: LeafletWidget,
    };
});