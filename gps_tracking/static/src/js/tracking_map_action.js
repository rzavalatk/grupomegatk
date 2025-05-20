odoo.define('gps_tracking.tracking_map_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomMapMenu = AbstractAction.extend({
        template: 'TrackingMap',

        map: null,

        start: function () {
            console.log("funciona");
            // Llama al start del padre y, cuando termine, inicializa el mapa.
            // Aseguramos que el DOM del widget ya esté renderizado.
            return this._super.apply(this, arguments).then(() => {
                this._initLeafletMap();
            });
        },

        _initLeafletMap: function () {
            const mapContainer = this.$('#map')[0]; // Obtiene la referencia al elemento DOM
            if (mapContainer) {
                if (!this.map) {
                    // Usa la referencia al elemento DOM directamente
                    this.map = L.map(mapContainer).setView([14.0989839, -87.1899595], 13);

                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; OpenStreetMap contributors'
                    }).addTo(this.map);

                    L.marker([14.0989839, -87.1899595]).addTo(this.map)
                        .bindPopup('Ubicación inicial')
                        .openPopup();
                    
                    // AÑADE ESTA LÍNEA AQUÍ:
                    this.map.invalidateSize(); // Asegura que el mapa recalcule su tamaño
                    console.log("Mapa Leaflet inicializado y tamaño invalidado.");

                } else {
                    // Si el mapa ya existe, solo ajusta la vista o añade/actualiza marcadores
                    this.map.setView([14.0989839, -87.1899595], 13);
                    // También podrías llamar a invalidateSize() aquí si el tamaño del contenedor pudo haber cambiado.
                    this.map.invalidateSize();
                    console.log("Mapa Leaflet actualizado y tamaño invalidado.");
                }
            } else {
                console.error("No se pudo encontrar el contenedor del mapa (#map).");
            }
        },

        destroy: function () {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
            this._super.apply(this, arguments);
            console.log("CustomMapMenu destruido y mapa removido.");
        }
    });

    core.action_registry.add('gps_map_tag', CustomMapMenu);
    return CustomMapMenu;
});