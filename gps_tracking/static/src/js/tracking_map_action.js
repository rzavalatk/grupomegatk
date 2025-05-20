odoo.define('gps_tracking.tracking_map_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomMapMenu = AbstractAction.extend({
        template: 'TrackingMap',

        map: null,

        start: function () {
            console.log("funciona");
            return this._super.apply(this, arguments).then(() => {
                this._initLeafletMap();
            });
        },

        _initLeafletMap: function () {
            // Espera a que el DOM esté cargado
            const mapContainer = this.$('#map')[0];
            if(mapContainer){
                if (!this.map) {
                    const map = L.map(mapContainer).setView([14.0989839, -87.1899595], 13); // Ciudad de México
        
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; OpenStreetMap contributors'
                    }).addTo(map);
        
                    L.marker([14.0989839, -87.1899595]).addTo(map)
                        .bindPopup('Ubicación inicial')
                        .openPopup();
                        
                    this.map.invalidateSize();
                } else {
                    this.map.setView([14.0989839, -87.1899595], 13);
                    this.map.invalidateSize();
                }
            } else {
                console.error("No se pudo encontrar el contenedor del mapa");
            }  
        },

        destroy: function () {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
            this._super.apply(this, arguments);
        }
    });

    core.action_registry.add('gps_map_tag', CustomMapMenu);  // Este es el tag que se llama en el XML
    return CustomMapMenu;
});
