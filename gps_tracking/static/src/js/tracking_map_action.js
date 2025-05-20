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
            const mapContainer = this.$('#map')[0];
            if (mapContainer) {
                // Solo inicializamos el mapa si aún no existe (es null o undefined)
                if (!this.map) {
                    try {
                        // Intentamos inicializar el mapa
                        this.map = L.map(mapContainer).setView([14.0989839, -87.1899599], 13);
        
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '&copy; OpenStreetMap contributors'
                        }).addTo(this.map);
        
                        L.marker([14.0989839, -87.1899599]).addTo(this.map)
                            .bindPopup('Ubicación inicial')
                            .openPopup();
                        
                        // Si la inicialización fue exitosa y this.map ya no es null,
                        // entonces podemos llamar a invalidateSize().
                        this.map.invalidateSize();
                        console.log("Mapa Leaflet inicializado y tamaño invalidado.");
        
                    } catch (e) {
                        // Captura cualquier error durante la inicialización de L.map
                        console.error("Error al inicializar el mapa Leaflet:", e);
                        this.map = null; // Asegura que this.map sea null si falla la inicialización
                    }
                } else {
                    // Si el mapa ya existe (this.map no es null), solo actualizamos la vista
                    // y aseguramos que el tamaño sea correcto.
                    this.map.setView([14.0989839, -87.1899599], 13);
                    this.map.invalidateSize();
                    console.log("Mapa Leaflet existente actualizado y tamaño invalidado.");
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
        }
    });

    core.action_registry.add('gps_map_tag', CustomMapMenu);  // Este es el tag que se llama en el XML
    return CustomMapMenu;
});
