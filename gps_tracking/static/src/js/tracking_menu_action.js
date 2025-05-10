odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',  // <-- Esto es importante
        start: function () {
            console.log("funciona");
            this._initLeafletMap();
            return this._super.apply(this, arguments);
        },

        _initLeafletMap: function () {
            // Espera a que el DOM esté cargado
            setTimeout(() => {
                const map = L.map('map').setView([19.4326, -99.1332], 13); // Ciudad de México

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors'
                }).addTo(map);

                L.marker([19.4326, -99.1332]).addTo(map)
                    .bindPopup('Ubicación inicial')
                    .openPopup();
            }, 0);
        },
    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);  // Este es el tag que se llama en el XML
    return CustomCardMenu;
});
