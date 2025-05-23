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
                    this.map = L.map(mapContainer).setView([14.099034869047827, -87.18985301661215], 6);

                    // Cargar mapa base de OpenStreetMap
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                    }).addTo(this.map);

                    // Lista de coordenadas de la ruta
                    var puntosRuta = [
                        [14.099594878975303, -87.18943253224012],
                        [14.099911084505052, -87.1892314310185],
                        [14.099931770832434, -87.1887134430254],
                        [14.099952457161839, -87.18800654174075]
                    ];

                    // Dibujar la ruta con una polilínea
                    var ruta = L.polyline(puntosRuta, {
                    color: '#0099ff',
                    weight: 5,
                    opacity: 1,
                    smoothFactor: 1,
                    className: 'my-route-line'
                    }).addTo(this.map);

                    for (var i = 0; i < puntosRuta.length; i++) {
                        L.marker(puntosRuta[i]).addTo(this.map);
                    }

                    // Ajustar el zoom para mostrar toda la ruta
                    this.map.fitBounds(ruta.getBounds());
                    
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