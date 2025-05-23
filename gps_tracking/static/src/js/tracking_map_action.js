odoo.define('gps_tracking.tracking_map_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomMapMenu = AbstractAction.extend({
        template: 'TrackingMap',
        map: null,

        start: function () {
            console.log("funciona");
            // No necesitamos llamar a _initLeafletMap directamente aquí,
            // ya que lo haremos en on_attach_callback para mayor seguridad.
            return this._super.apply(this, arguments);
        },

        // Este método se llama cuando el widget se inserta en el DOM y está visible.
        on_attach_callback: function () {
            // Asegúrate de que el mapa se inicialice solo una vez.
            if (!this.map) {
                this._initLeafletMap();
            } else {
                // Si el mapa ya existe (e.g., el widget fue temporalmente oculto y ahora se muestra de nuevo),
                // asegúrate de que su tamaño sea invalidado.
                this.map.invalidateSize();
            }
            console.log("on_attach_callback llamado. Mapa debería estar visible y correcto.");
        },

        _initLeafletMap: function () {
            const mapContainer = this.$('#map')[0];
            if (mapContainer) {
                try {
                    var map = L.map(mapContainer).setView([20.0, -100.0], 6);

                    // Cargar mapa base de OpenStreetMap
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                    }).addTo(map);

                    // Lista de coordenadas de la ruta
                    var puntosRuta = [
                    [20.0, -100.0],
                    [20.5, -100.3],
                    [21.0, -100.5],
                    [21.5, -100.2]
                    ];

                    // Dibujar la ruta con una polilínea
                    var ruta = L.polyline(puntosRuta, {
                    color: 'black',
                    weight: 4,
                    opacity: 0.7,
                    smoothFactor: 1
                    }).addTo(map);

                    // Ajustar el zoom para mostrar toda la ruta
                    map.fitBounds(ruta.getBounds());
                    
                    // Llama a invalidateSize() aquí también, por si acaso.
                    // on_attach_callback ya garantiza la visibilidad, pero no está de más.
                    this.map.invalidateSize();
                    console.log("Mapa Leaflet inicializado y tamaño invalidado.");

                } catch (e) {
                    console.error("Error al inicializar el mapa Leaflet:", e);
                    this.map = null;
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