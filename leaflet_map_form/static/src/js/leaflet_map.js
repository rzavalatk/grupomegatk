odoo.define('leaflet_map_form.leaflet_map', function (require) {
    // const FormController = require('web.FormController');

    // const LeafletFormController = FormController.include({
    //     _renderView: async function () {
    //         await this._super(...arguments);
    //         console.log("1");
            
    //         this._renderLeafletMap();
    //     },

    //     _renderLeafletMap: function () {
    //         console.log("2");
    //         const record = this.model.get(this.handle);
    //         const lat = record.data.latitude;
    //         const lng = record.data.longitude;

    //         const container = document.getElementById("leaflet_map_container");
    //         if (!container || !lat || !lng) return;

    //         if (container._leaflet_map_initialized) return;
    //         container._leaflet_map_initialized = true;

    //         const map = L.map(container).setView([lat, lng], 13);
    //         L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    //             attribution: '© OpenStreetMap'
    //         }).addTo(map);

    //         L.marker([lat, lng]).addTo(map).bindPopup("Ubicación").openPopup();
    //     }
    // });
"use strict";
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
 
});