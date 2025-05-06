odoo.define('gps_tracking.trip_map', function (require) {
    "use strict";

    const FormController = require('web.FormController');
    const viewRegistry = require('web.view_registry');
    const FormView = require('web.FormView');

    const TripMapController = FormController.extend({
        renderButtons: function () {
            this._super.apply(this, arguments);
            const recordId = this.initialState.data.id;

            this._rpc({
                model: 'gps.device.trip',
                method: 'get_trip_coordinates',
                args: [[recordId]],
            }).then(coords => {
                console.log(coords);
                
                this.renderMap(coords);
            });
        },

        renderMap: function (coords) {
            if (!coords.length) return;
            const map = L.map('trip_map').setView([coords[0].lat, coords[0].lng], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);

            const latlngs = coords.map(p => [p.lat, p.lng]);
            L.polyline(latlngs, { color: 'blue' }).addTo(map);
            L.marker(latlngs[0]).addTo(map).bindPopup("Inicio").openPopup();
            L.marker(latlngs[latlngs.length - 1]).addTo(map).bindPopup("Fin");
        },
    });

    const TripMapView = FormView.extend({
        config: Object.assign({}, FormView.prototype.config, {
            Controller: TripMapController,
        }),
    });

    viewRegistry.add('trip_map_view', TripMapView);
});
