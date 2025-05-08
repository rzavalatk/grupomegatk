odoo.define('gps_tracking.LeafletTripMap', function (require) {
    "use strict";

    const Widget = require('web.Widget');
    const rpc = require('web.rpc');

    const LeafletTripMap = Widget.extend({
        template: 'gps_tracking.LeafletMap',

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.tripId = options.trip_id;
        },

        willStart: function () {
            return this._loadLocations();
        },

        start: function () {
            this._super.apply(this, arguments);
            return this._initMap();
        },

        _loadLocations: function () {
            var self = this;
            return rpc.query({
                model: 'gps.device.location',
                method: 'search_read',
                args: [[['trip_id', '=', this.tripId]], ['latitude', 'longitude', 'timestamp']],
            }).then(function (locations) {
                self.locations = locations;
            });
        },

        _initMap: function () {
            if (!this.locations || this.locations.length === 0) {
                this.$el.html("<div class='alert alert-info'>No hay ubicaciones registradas para este viaje.</div>");
                return;
            }

            var points = this.locations.map(function (loc) {
                return [parseFloat(loc.latitude), parseFloat(loc.longitude)];
            });

            this.map = L.map(this.el).setView(points[0], 13);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(this.map);

            var polyline = L.polyline(points, {
                color: 'blue',
                weight: 4,
                opacity: 0.7,
                smoothFactor: 1
            }).addTo(this.map);

            if (points.length > 0) {
                L.marker(points[0]).addTo(this.map).bindPopup("Inicio del viaje").openPopup();
                L.marker(points[points.length - 1]).addTo(this.map).bindPopup("Última posición registrada");
            }

            this.map.fitBounds(polyline.getBounds());
        }
    });

    return LeafletTripMap;
});
