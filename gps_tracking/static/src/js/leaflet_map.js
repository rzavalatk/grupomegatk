odoo.define('gps_tracking.LeafletTripMap', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var FieldRegistry = require('web.field_registry');
    var {registry} = require('@web/core/registry');

    var LeafletTripMap = Widget.extend({
        template: 'gps_tracking.LeafletMap',
        
        init: function(parent, options) {
            this._super(parent);
            this.tripId = options.trip_id;
        },
        
        willStart: function() {
            return this._loadLocations();
        },
        
        start: function() {
            this._super.apply(this, arguments);
            return this._initMap();
        },
        
        _loadLocations: function() {
            var self = this;
            return rpc.query({
                model: 'gps.device.location',
                method: 'search_read',
                args: [[['trip_id', '=', this.tripId]], ['latitude', 'longitude', 'timestamp']],
            }).then(function(locations) {
                self.locations = locations;
            });
        },
        
        _initMap: function() {
            if (!this.locations || this.locations.length === 0) {
                this.$el.html("<div class='alert alert-info'>No hay ubicaciones registradas para este viaje.</div>");
                return;
            }

            // Convertir coordenadas a números
            var points = this.locations.map(function(loc) {
                return [parseFloat(loc.latitude), parseFloat(loc.longitude)];
            });

            // Crear el mapa centrado en el primer punto
            this.map = L.map(this.$el[0]).setView(points[0], 13);

            // Añadir capa de tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.map);

            // Crear una línea que conecta todos los puntos
            var polyline = L.polyline(points, {
                color: 'blue',
                weight: 4,
                opacity: 0.7,
                smoothFactor: 1
            }).addTo(this.map);

            // Añadir marcadores para el inicio y fin
            if (points.length > 0) {
                L.marker(points[0]).addTo(this.map)
                    .bindPopup("Inicio del viaje")
                    .openPopup();
                
                L.marker(points[points.length - 1]).addTo(this.map)
                    .bindPopup("Última posición registrada");
            }

            // Ajustar el zoom para mostrar toda la ruta
            this.map.fitBounds(polyline.getBounds());
        }
    });

    // Registra el widget en el registro de campos
    // FieldRegistry.add('leaflet_trip_map', LeafletTripMap);
    registry.category('components').add('leaflet_trip_map', LeafletTripMap);

    return LeafletTripMap;
});